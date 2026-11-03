import io
import json
import re
from urllib.parse import parse_qs, urlsplit

import pytest

import telegram_bot
from test_app import app, client, token  # noqa: F401  (pytest fixtures)
from test_shop import add_to_cart, query  # noqa: F401

CHAT, USER = 7001, 7001


@pytest.fixture
def bot(app, monkeypatch):
    """Configure the bot and record every Bot API call instead of contacting Telegram."""
    app.config.update(TELEGRAM_BOT_TOKEN='123:test', TELEGRAM_BOT_USERNAME='EmpressTestBot')
    calls = []

    def fake_api(token, method, http_timeout=15, **params):
        calls.append((method, params))
        return {'message_id': len(calls)}

    monkeypatch.setattr(telegram_bot, 'api', fake_api)
    return calls


def update(text=None, contact=None, chat_id=CHAT, sender=USER, chat_type='private'):
    message = {'chat': {'id': chat_id, 'type': chat_type}, 'from': {'id': sender}}
    if text is not None:
        message['text'] = text
    if contact is not None:
        message['contact'] = contact
    return {'update_id': 1, 'message': message}


def request_code(client, phone='012 345 678', next_path=None):
    data = {'csrf_token': token(client, '/account/login'), 'phone': phone}
    if next_path:
        data['next'] = next_path
    response = client.post('/account/login', data=data)
    assert response.status_code == 303
    page = client.get(response.location).text
    link = re.search(r'href="(https://t\.me/EmpressTestBot\?start=[^"]+)"', page)[1]
    return page, parse_qs(urlsplit(link).query)['start'][0]


def sent_code(calls):
    return re.search(r'code: (\d{6})', calls[-1][1]['text'])[1]


def test_first_sign_in_shares_contact_then_gets_code(client, app, bot):
    page, start = request_code(client)
    assert 'Press START' in page and 'Open Telegram' in page
    # Typing a code before the bot has sent one gives a clear message.
    response = client.post('/account/verify', data={'csrf_token': token(client, '/account/verify'), 'code': '123456'})
    assert response.status_code == 422 and 'Open Telegram first' in response.text
    telegram_bot.handle_update(app, update(f'/start {start}'))
    method, params = bot[-1]
    assert method == 'sendMessage' and params['reply_markup']['keyboard'][0][0]['request_contact'] is True
    telegram_bot.handle_update(app, update(contact={'phone_number': '85512345678', 'user_id': USER}))
    assert bot[-1][1]['chat_id'] == CHAT and bot[-1][1]['reply_markup'] == {'remove_keyboard': True}
    code = sent_code(bot)
    assert 'We sent a code to your Telegram' in client.get('/account/verify').text
    response = client.post('/account/verify', data={'csrf_token': token(client, '/account/verify'), 'code': code})
    assert response.location == '/account'
    assert query(app, 'SELECT phone,chat_id FROM telegram_chats') == [('+85512345678', CHAT)]


def test_returning_customer_gets_code_immediately(client, app, bot):
    with app.app_context():
        from app import db
        db().execute('INSERT INTO telegram_chats(phone,chat_id,updated_at) VALUES(?,?,0)', ('+85512345678', CHAT))
        db().commit()
    page, _ = request_code(client)
    assert 'We sent a code to your Telegram' in page
    assert bot[-1][0] == 'sendMessage' and bot[-1][1]['chat_id'] == CHAT
    response = client.post('/account/verify', data={'csrf_token': token(client, '/account/verify'), 'code': sent_code(bot)})
    assert response.location == '/account'


def test_someone_elses_number_never_gets_a_code(client, app, bot):
    _, start = request_code(client, '011 111 111')
    telegram_bot.handle_update(app, update(f'/start {start}'))
    # A forwarded contact card is refused.
    telegram_bot.handle_update(app, update(contact={'phone_number': '85511111111', 'user_id': 999}))
    assert 'your own number' in bot[-1][1]['text']
    # The sender's real number differs from the one typed on the website.
    telegram_bot.handle_update(app, update(contact={'phone_number': '+85522222222', 'user_id': USER}))
    assert '+85522222222' in bot[-1][1]['text'] and 'code:' not in bot[-1][1]['text']
    assert query(app, "SELECT count(*) FROM login_codes WHERE code_hash!=''") == [(0,)]


def test_stale_links_groups_and_unknown_messages(client, app, bot):
    telegram_bot.handle_update(app, update('/start'))
    telegram_bot.handle_update(app, update('/start not-a-real-token'))
    assert all('expired' in params['text'] for _, params in bot)
    _, start = request_code(client)
    calls_before = len(bot)
    telegram_bot.handle_update(app, update(f'/start {start}', chat_type='group'))
    telegram_bot.handle_update(app, update('hello'))
    assert len(bot) == calls_before
    telegram_bot.handle_update(app, update(contact={'phone_number': '85512345678', 'user_id': USER}, chat_id=4242, sender=USER))
    assert 'expired' in bot[-1][1]['text']


def test_checkout_redirect_survives_bot_sign_in(client, app, bot):
    add_to_cart(client)
    login_page = client.get('/checkout').location
    _, start = request_code(client, next_path='/checkout')
    telegram_bot.handle_update(app, update(f'/start {start}'))
    telegram_bot.handle_update(app, update(contact={'phone_number': '85512345678', 'user_id': USER}))
    verify = '/account/verify?next=/checkout'
    assert '/account/login' in login_page
    assert client.post(verify, data={'csrf_token': token(client, verify), 'code': sent_code(bot)}).location == '/checkout'


def test_webhook_requires_telegram_secret(client, app, bot):
    _, start = request_code(client)
    update_json = update(f'/start {start}')
    assert client.post('/telegram/webhook', json=update_json).status_code == 403
    assert client.post('/telegram/webhook', json=update_json, headers={'X-Telegram-Bot-Api-Secret-Token': 'wrong'}).status_code == 403
    assert not bot or bot[-1][0] != 'sendMessage' or 'Share' not in bot[-1][1]['text']
    secret = {'X-Telegram-Bot-Api-Secret-Token': telegram_bot.webhook_secret('123:test')}
    # No CSRF token is needed: Telegram's secret header authenticates the call.
    assert client.post('/telegram/webhook', json=update_json, headers=secret).status_code == 200
    assert bot[-1][1]['reply_markup']['keyboard'][0][0]['request_contact'] is True
    assert client.post('/telegram/webhook', json={'nonsense': True}, headers=secret).status_code == 200


def test_bot_api_and_polling(app, monkeypatch):
    requests, webhook_url = [], ['']

    def fake_urlopen(request, timeout):
        requests.append((request.full_url, json.loads(request.data)))
        method = request.full_url.rsplit('/', 1)[1]
        result = {'getMe': {'username': 'EmpressRealBot'}, 'getWebhookInfo': {'url': webhook_url[0]}}.get(method, [])
        return io.BytesIO(json.dumps({'ok': True, 'result': result}).encode())

    monkeypatch.setattr(telegram_bot, 'urlopen', fake_urlopen)
    monkeypatch.setattr(telegram_bot.threading, 'Thread', lambda **kwargs: type('T', (), {'start': lambda self: None})())
    app.config.update(TELEGRAM_BOT_TOKEN='123:abc', TELEGRAM_BOT_USERNAME='')
    assert telegram_bot.start_polling(app) is True
    assert app.config['TELEGRAM_BOT_USERNAME'] == 'EmpressRealBot'
    assert requests[0][0] == 'https://api.telegram.org/bot123:abc/getMe'
    # When the live site owns the bot, a local copy must not poll (that would require removing its webhook).
    webhook_url[0] = 'https://empresscambodia.vercel.app/telegram/webhook'
    assert telegram_bot.start_polling(app) is False
    assert not any(url.endswith('/deleteWebhook') for url, _ in requests)
    telegram_bot.set_webhook(app, 'https://shop.example/')
    assert requests[-1][1]['url'] == 'https://shop.example/telegram/webhook'
    assert requests[-1][1]['secret_token'] == telegram_bot.webhook_secret('123:abc')
    monkeypatch.setattr(telegram_bot, 'urlopen', lambda request, timeout: io.BytesIO(b'{"ok": false, "description": "Unauthorized"}'))
    with pytest.raises(telegram_bot.TelegramError, match='Unauthorized'):
        telegram_bot.api('bad', 'getMe')
    assert telegram_bot.start_polling(app) is False
