"""ABA PayWay checkout: signed purchase requests and server-side payment verification.

Docs: https://developer.payway.com.kh/purchase-14530820e0.md and
https://developer.payway.com.kh/check-transaction-14530826e0.md
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen

PURCHASE_PATH = '/api/payment-gateway/v1/payments/purchase'
CHECK_PATH = '/api/payment-gateway/v1/payments/check-transaction-2'
# PayWay's Cloudflare front end rejects Python's default user agent (error 1010).
USER_AGENT = 'Mozilla/5.0 (compatible; EmpressCambodiaShop/1.0)'
# Order of fields in the purchase hash, exactly as documented by ABA.
PURCHASE_HASH_FIELDS = ('req_time', 'merchant_id', 'tran_id', 'amount', 'items', 'shipping', 'firstname', 'lastname', 'email', 'phone',
                        'type', 'payment_option', 'return_url', 'cancel_url', 'continue_success_url', 'return_deeplink', 'currency',
                        'custom_fields', 'return_params', 'payout', 'lifetime', 'additional_params', 'google_pay_token', 'skip_success_page')


class PayWayError(Exception):
    pass


def enabled(config):
    return bool(config['PAYWAY_MERCHANT_ID'] and config['PAYWAY_API_KEY'])


def sign(api_key, text):
    """Base64 of the raw HMAC-SHA512 of text, keyed with the merchant API key."""
    return base64.b64encode(hmac.new(api_key.encode(), text.encode(), hashlib.sha512).digest()).decode()


def b64json(value):
    return base64.b64encode(json.dumps(value, ensure_ascii=False).encode()).decode()


def request_time():
    return datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')


def new_tran_id(order_id):
    """Digits only and at most 20 characters; every payment attempt needs a fresh ID."""
    return f'{order_id}{int(time.time())}{secrets.randbelow(100):02d}'[:20]


def money(cents):
    return f'{cents / 100:.2f}'


def purchase_form(config, tran_id, order, items, return_url, cancel_url, continue_url):
    """Fields for the HTML form that sends the customer to the PayWay checkout."""
    first, _, last = order['name'].partition(' ')
    fields = {
        'req_time': request_time(), 'merchant_id': config['PAYWAY_MERCHANT_ID'], 'tran_id': tran_id,
        'amount': money(order['total_cents']),
        'items': b64json([{'name': item['name'], 'quantity': item['quantity'], 'price': float(money(item['unit_cents']))} for item in items]),
        'firstname': first[:100], 'lastname': last[:100], 'email': order['email'][:50], 'phone': order['phone'][:20],
        'payment_option': config['PAYWAY_PAYMENT_OPTION'],
        'return_url': base64.b64encode(return_url.encode()).decode(), 'cancel_url': cancel_url, 'continue_success_url': continue_url,
        'currency': config['PAYWAY_CURRENCY'], 'return_params': str(order['id']), 'skip_success_page': '1',
    }
    fields['hash'] = sign(config['PAYWAY_API_KEY'], ''.join(fields.get(name, '') for name in PURCHASE_HASH_FIELDS))
    # Not part of the hash. Without it, profiles that also have the QR API get JSON back instead of the checkout page.
    fields['payment_gate'] = '0'
    return {name: value for name, value in fields.items() if value != ''}


def check_transaction(config, tran_id):
    """Ask PayWay for the current status of a transaction. Returns the parsed JSON response."""
    body = {'req_time': request_time(), 'merchant_id': config['PAYWAY_MERCHANT_ID'], 'tran_id': tran_id}
    body['hash'] = sign(config['PAYWAY_API_KEY'], body['req_time'] + body['merchant_id'] + tran_id)
    request = Request(config['PAYWAY_BASE_URL'].rstrip('/') + CHECK_PATH, data=json.dumps(body).encode(),
                      headers={'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': USER_AGENT})
    try:
        with urlopen(request, timeout=15) as response:
            return json.load(response)
    except (OSError, ValueError) as error:
        raise PayWayError(str(error)) from error


def is_approved(result, amount_cents):
    """True only when PayWay reports an approved payment for the full original order amount."""
    status, data = result.get('status') or {}, result.get('data') or {}
    if str(status.get('code')) not in ('0', '00') or data.get('payment_status') != 'APPROVED':
        return False
    try:
        # original_amount is in the order's currency, even if the customer paid from an account in another currency.
        return round(float(data['original_amount']) * 100) == amount_cents
    except (KeyError, TypeError, ValueError):
        return False
