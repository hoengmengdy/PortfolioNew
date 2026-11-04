import io
import re
import json

import pytest

import app as app_module
from app import normalize_phone
from test_app import app, client, connect_db, token  # noqa: F401  (pytest fixtures)
from test_shop import add_to_cart, order_form, query, sign_in, telegram_codes  # noqa: F401

# The autouse fixture replaces the sender, so keep the real one for the gateway test.
real_send_telegram_code = app_module.send_telegram_code


@pytest.mark.parametrize('raw,expected', [
    ('012 345 678', '+85512345678'), ('012-345-678', '+85512345678'), ('85512345678', '+85512345678'),
    ('+855 12 345 678', '+85512345678'), ('0085512345678', '+85512345678'), ('+1 (415) 555-0100', '+14155550100'),
    ('abc', None), ('012', None), ('', None), ('+0123456789', None)])
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


def test_sign_in_with_telegram_code(client, app, telegram_codes):
    assert '/account/login' in client.get('/account').location
    assert client.get('/account/verify').status_code == 302
    response = client.post('/account/login', data={'csrf_token': token(client, '/account/login'), 'phone': '012 345 678'})
    assert response.status_code == 303 and '/account/verify' in response.location
    phone, code = telegram_codes[-1]
    assert phone == '+85512345678' and len(code) == 6 and code.isdigit()
    # Only a hash of the code is stored.
    assert code not in str(query(app, 'SELECT * FROM login_codes'))
    page = client.get('/account/verify').text
    assert '+85512345678' in page and 'autocomplete="one-time-code"' in page
    wrong = '000000' if code != '000000' else '111111'
    assert client.post('/account/verify', data={'csrf_token': token(client, '/account/verify'), 'code': wrong}).status_code == 422
    response = client.post('/account/verify', data={'csrf_token': token(client, '/account/verify'), 'code': code})
    assert response.status_code == 303 and response.location == '/account'
    assert '+85512345678' in client.get('/account').text
    assert query(app, 'SELECT phone FROM customers') == [('+85512345678',)]
    assert query(app, 'SELECT count(*) FROM login_codes') == [(0,)]
    client.post('/account/logout', data={'csrf_token': token(client, '/account')})
    assert '/account/login' in client.get('/account').location


def test_code_attempts_expiry_and_resend_limits(client, app, telegram_codes):
    csrf = token(client, '/account/login')
    assert client.post('/account/login', data={'csrf_token': csrf, 'phone': 'not a phone'}).status_code == 422
    client.post('/account/login', data={'csrf_token': csrf, 'phone': '012345678'})
    code = telegram_codes[-1][1]
    wrong = '000000' if code != '000000' else '111111'
    for _ in range(5):
        assert client.post('/account/verify', data={'csrf_token': csrf, 'code': wrong}).status_code == 422
    # The right code no longer works after five wrong guesses.
    response = client.post('/account/verify', data={'csrf_token': csrf, 'code': code})
    assert response.status_code == 429 and 'Too many wrong attempts' in response.text
    response = client.post('/account/login', data={'csrf_token': csrf, 'phone': '012345678'})
    assert response.status_code == 429 and 'wait a minute' in response.text
    assert len(telegram_codes) == 1
    with connect_db(app) as connection:
        connection.execute('UPDATE login_codes SET created_at=created_at-120, expires_at=expires_at-400, attempts=0')
    response = client.post('/account/verify', data={'csrf_token': csrf, 'code': code})
    assert response.status_code == 422 and 'expired' in response.text
    assert client.post('/account/login', data={'csrf_token': csrf, 'phone': '012345678'}).status_code == 303
    assert len(telegram_codes) == 2


def test_telegram_failure_and_redirect_target(client, app, telegram_codes, monkeypatch):
    monkeypatch.setattr(app_module, 'send_telegram_code', lambda phone, code: False)
    response = client.post('/account/login', data={'csrf_token': token(client, '/account/login'), 'phone': '012345678'})
    assert response.status_code == 502 and 'could not send a Telegram code' in response.text
    assert query(app, 'SELECT count(*) FROM login_codes') == [(0,)]
    monkeypatch.setattr(app_module, 'send_telegram_code', lambda phone, code: telegram_codes.append((phone, code)) or True)
    client.post('/account/login', data={'csrf_token': token(client, '/account/login'), 'phone': '012345678', 'next': 'https://evil.example'})
    response = client.post('/account/verify', data={'csrf_token': token(client, '/account/verify'), 'code': telegram_codes[-1][1]})
    assert response.location == '/account'
    client.post('/account/logout', data={'csrf_token': token(client, '/account')})
    with connect_db(app) as connection:
        connection.execute('DELETE FROM login_codes')
    add_to_cart(client)
    login_page = '/account/login?next=/checkout'
    assert login_page in client.get('/checkout').text
    client.post('/account/login', data={'csrf_token': token(client, login_page), 'phone': '012345678', 'next': '/checkout'})
    verify_page = '/account/verify?next=/checkout'
    response = client.post(verify_page, data={'csrf_token': token(client, verify_page), 'code': telegram_codes[-1][1]})
    assert response.location == '/checkout'
    with client.session_transaction() as session:
        assert session['cart'] == {'1': 2}


def test_accounts_only_see_their_own_orders(app, telegram_codes):
    first, second = app.test_client(), app.test_client()
    sign_in(first, telegram_codes, '011 111 111')
    add_to_cart(first)
    order_url = first.post('/checkout', data=order_form(first)).location
    assert 'Order #1' in first.get('/account').text
    sign_in(second, telegram_codes, '022 222 222')
    assert 'no orders yet' in second.get('/account').text
    # Checkout reuses the customer's saved delivery address.
    add_to_cart(first)
    assert 'value="Sok"' in first.get('/checkout').text and 'value="Dara"' in first.get('/checkout').text
    assert first.get(order_url).status_code == 200


def test_gateway_request(app, monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured.update(url=request.full_url, headers=dict(request.header_items()), body=json.loads(request.data), timeout=timeout)
        return io.BytesIO(json.dumps({'ok': True, 'result': {'request_id': 'r1'}}).encode())

    monkeypatch.setattr(app_module, 'urlopen', fake_urlopen)
    app.config.update(TELEGRAM_GATEWAY_TOKEN='secret-token', TELEGRAM_DEV_MODE=False)
    with app.app_context():
        assert real_send_telegram_code('+85512345678', '123456') is True
        assert captured['url'] == 'https://gatewayapi.telegram.org/sendVerificationMessage'
        assert captured['headers']['Authorization'] == 'Bearer secret-token'
        assert captured['body'] == {'phone_number': '+85512345678', 'code': '123456', 'ttl': 300}
        monkeypatch.setattr(app_module, 'urlopen', lambda request, timeout: io.BytesIO(b'{"ok": false, "error": "ACCESS_TOKEN_INVALID"}'))
        assert real_send_telegram_code('+85512345678', '123456') is False

        def broken(request, timeout):
            raise OSError('network down')
        monkeypatch.setattr(app_module, 'urlopen', broken)
        assert real_send_telegram_code('+85512345678', '123456') is False
        app.config['TELEGRAM_GATEWAY_TOKEN'] = ''
        assert real_send_telegram_code('+85512345678', '123456') is False
        app.config['TELEGRAM_DEV_MODE'] = True
        assert real_send_telegram_code('+85512345678', '123456') is True


def test_retries_do_not_lock_people_out(client, telegram_codes):
    csrf = token(client, '/account/login')
    # One code sent, then repeated retries and typos: none of these use up the per-address quota.
    assert client.post('/account/login', data={'csrf_token': csrf, 'phone': '015663024'}).status_code == 303
    for _ in range(12):
        response = client.post('/account/login', data={'csrf_token': csrf, 'phone': '015663024'})
        assert response.status_code == 429 and 'wait a minute' in response.text and 'id="phone"' in response.text
        assert client.post('/account/login', data={'csrf_token': csrf, 'phone': 'oops'}).status_code == 422
    # Four more numbers reach five codes sent from this address in a minute.
    for number in range(4):
        assert client.post('/account/login', data={'csrf_token': csrf, 'phone': f'01133300{number}'}).status_code == 303
    response = client.post('/account/login', data={'csrf_token': csrf, 'phone': '011333009'})
    # The sign-in form stays visible with an explanation instead of an error page.
    assert response.status_code == 429 and 'Too many requests' in response.text and 'id="phone"' in response.text
    assert len(telegram_codes) == 5


def test_dev_mode_shows_code_on_screen(app, monkeypatch):
    monkeypatch.setattr(app_module, 'send_telegram_code', real_send_telegram_code)
    app.config.update(TELEGRAM_GATEWAY_TOKEN='', TELEGRAM_DEV_MODE=True)
    client = app.test_client()
    client.post('/account/login', data={'csrf_token': token(client, '/account/login'), 'phone': '015663024'})
    page = client.get('/account/verify').text
    code = re.search(r'Your code is: (\d{6})', page)[1]
    assert client.post('/account/verify', data={'csrf_token': token(client, '/account/verify'), 'code': code}).location == '/account'
