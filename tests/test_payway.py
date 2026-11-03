import base64
import hashlib
import hmac
import io
import json
import re

import pytest

import payway
from test_app import app, client, token  # noqa: F401  (pytest fixtures)
from test_shop import add_to_cart, order_form, query, sign_in, telegram_codes  # noqa: F401

API_KEY = 'test-api-key'


@pytest.fixture
def shop(app, client, telegram_codes, monkeypatch):
    """A signed-in customer with PayWay enabled; returns the list of transaction checks made."""
    app.config.update(PAYWAY_MERCHANT_ID='ec000002', PAYWAY_API_KEY=API_KEY, PAYWAY_BASE_URL='https://checkout-sandbox.payway.com.kh')
    sign_in(client, telegram_codes)
    checks = []
    monkeypatch.setattr(payway, 'check_transaction', lambda config, tran_id: checks.append(tran_id) or checks_result[0])
    checks_result = [{'status': {'code': 6, 'message': 'Transaction not found'}}]
    return checks, checks_result


def approved(amount):
    return {'status': {'code': '00', 'message': 'Success!'}, 'data': {'payment_status': 'APPROVED', 'original_amount': amount, 'apv': '753786'}}


def place_payway_order(client):
    add_to_cart(client)
    response = client.post('/checkout', data=order_form(client, payment_method='payway'))
    assert response.status_code == 303 and response.location.endswith('/pay')
    return response.location


def form_fields(html):
    return dict(re.findall(r'<input type="hidden" name="([a-z_]+)" value="([^"]*)">', html))


def test_payway_is_offered_only_when_configured(client, app, shop):
    add_to_cart(client)
    assert 'ABA PayWay' in client.get('/checkout').text
    app.config['PAYWAY_API_KEY'] = ''
    assert 'ABA PayWay' not in client.get('/checkout').text
    assert client.post('/checkout', data=order_form(client, payment_method='payway')).status_code == 422


def test_checkout_sends_signed_request_to_payway(client, app, shop):
    pay_url = place_payway_order(client)
    response = client.get(pay_url)
    html = response.text
    assert 'action="https://checkout-sandbox.payway.com.kh/api/payment-gateway/v1/payments/purchase"' in html
    assert 'data-autosubmit' in html
    assert "form-action 'self' https://checkout-sandbox.payway.com.kh" in response.headers['Content-Security-Policy']
    fields = {name: value.replace('&#43;', '+').replace('&#34;', '"') for name, value in form_fields(html).items()}
    assert fields['amount'] == '37.50' and fields['merchant_id'] == 'ec000002' and fields['currency'] == 'USD'
    assert fields['firstname'] == 'Sok' and fields['lastname'] == 'Dara' and fields['phone'] == '+85512345678'
    assert base64.b64decode(fields['return_url']).decode() == 'http://localhost/payway/callback'
    assert json.loads(base64.b64decode(fields['items'])) == [{'name': 'The Daily Glow', 'quantity': 2, 'price': 18.0}]
    assert fields['tran_id'].isdigit() and len(fields['tran_id']) <= 20
    assert fields['payment_gate'] == '0'
    # Recompute the documented HMAC-SHA512 independently of payway.py.
    order = ['req_time', 'merchant_id', 'tran_id', 'amount', 'items', 'shipping', 'firstname', 'lastname', 'email', 'phone', 'type',
             'payment_option', 'return_url', 'cancel_url', 'continue_success_url', 'return_deeplink', 'currency', 'custom_fields',
             'return_params', 'payout', 'lifetime', 'additional_params', 'google_pay_token', 'skip_success_page']
    expected = base64.b64encode(hmac.new(API_KEY.encode(), ''.join(fields.get(k, '') for k in order).encode(), hashlib.sha512).digest()).decode()
    assert fields['hash'] == expected
    assert query(app, 'SELECT order_id,amount_cents,status FROM payway_transactions') == [(1, 3750, 'pending')]
    # Every visit makes a new transaction ID, as PayWay rejects duplicates.
    client.get(pay_url)
    assert query(app, 'SELECT count(DISTINCT tran_id) FROM payway_transactions') == [(2,)]


def test_order_is_paid_only_after_payway_confirms(client, app, shop):
    checks, result = shop
    order_url = place_payway_order(client).removesuffix('/pay')
    client.get(order_url + '/pay')
    page = client.get(order_url).text
    assert 'Pay with ABA PayWay' in page and len(checks) == 1
    # A wrong amount is never accepted.
    result[0] = approved(1.00)
    client.get(order_url)
    assert query(app, 'SELECT payment_status FROM orders') == [('unpaid',)]
    result[0] = approved(37.50)
    page = client.get(order_url).text
    assert 'Payment received with ABA PayWay' in page
    assert query(app, 'SELECT payment_status,payment_reference FROM orders')[0][0] == 'paid'
    assert 'APV 753786' in query(app, 'SELECT payment_reference FROM orders')[0][0]
    calls = len(checks)
    client.get(order_url)
    assert len(checks) == calls
    assert client.get(order_url + '/pay').location.endswith(order_url.rsplit('/', 1)[1])


def test_declined_attempt_and_callback(client, app, shop):
    checks, result = shop
    order_url = place_payway_order(client).removesuffix('/pay')
    client.get(order_url + '/pay')
    result[0] = {'status': {'code': '00'}, 'data': {'payment_status': 'DECLINED', 'original_amount': 37.5}}
    client.get(order_url)
    assert query(app, 'SELECT status FROM payway_transactions') == [('declined',)]
    client.get(order_url + '/pay')
    tran_id = query(app, "SELECT tran_id FROM payway_transactions WHERE status='pending'")[0][0]
    result[0] = approved(37.5)
    # The PayWay notice needs no CSRF token, and only triggers a server-side check.
    response = app.test_client().post('/payway/callback', json={'tran_id': tran_id, 'status': '0', 'apv': '000000'})
    assert response.status_code == 200 and checks[-1] == tran_id
    assert query(app, 'SELECT payment_status FROM orders') == [('paid',)]
    assert app.test_client().post('/payway/callback', json={'tran_id': 'unknown'}).status_code == 200


def test_check_transaction_request(app, monkeypatch):
    sent = {}

    def fake_urlopen(request, timeout):
        sent.update(url=request.full_url, body=json.loads(request.data), agent=request.get_header('User-agent'))
        return io.BytesIO(json.dumps(approved(1.5)).encode())

    monkeypatch.setattr(payway, 'urlopen', fake_urlopen)
    config = {'PAYWAY_MERCHANT_ID': 'ec000002', 'PAYWAY_API_KEY': API_KEY, 'PAYWAY_BASE_URL': 'https://checkout-sandbox.payway.com.kh/'}
    result = payway.check_transaction(config, '123')
    assert sent['url'] == 'https://checkout-sandbox.payway.com.kh/api/payment-gateway/v1/payments/check-transaction-2'
    assert sent['agent'].startswith('Mozilla/5.0')
    body = sent['body']
    assert body['hash'] == payway.sign(API_KEY, body['req_time'] + 'ec000002' + '123') and len(body['req_time']) == 14
    assert payway.is_approved(result, 150) and not payway.is_approved(result, 151)
    assert not payway.is_approved({'status': {'code': 6}}, 150)
    monkeypatch.setattr(payway, 'urlopen', lambda request, timeout: (_ for _ in ()).throw(OSError('down')))
    with pytest.raises(payway.PayWayError):
        payway.check_transaction(config, '123')
