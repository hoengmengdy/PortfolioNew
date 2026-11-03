"""Telegram bot that delivers customer sign-in codes for free.

A customer opens the bot from the sign-in page (t.me/<bot>?start=<token>), presses Start and shares
their own phone number with Telegram's contact button. The bot sends a code only when that verified
number matches the number typed on the website. Known chats get later codes straight away.
"""
import hashlib
import json
import logging
import re
import threading
import time
from contextlib import closing
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import database
from phone_codes import CODE_TTL, hash_code, new_code, normalize_phone

API_URL = 'https://api.telegram.org/bot{token}/{method}'
log = logging.getLogger(__name__)

CODE_MESSAGE = ('Empress Cambodia sign-in code: {code}\nIt expires in 5 minutes. Never share it with anyone.\n\n'
                'លេខកូដចូលគណនី Empress Cambodia៖ {code}\nផុតកំណត់ក្រោយ 5 នាទី។ កុំចែករំលែកលេខកូដនេះជាមួយអ្នកណាម្នាក់ឡើយ។')
SHARE_MESSAGE = ('Tap the button below to share your phone number. We only use it to confirm your sign-in.\n\n'
                 'សូមចុចប៊ូតុងខាងក្រោម ដើម្បីចែករំលែកលេខទូរស័ព្ទរបស់អ្នក។ យើងប្រើវាសម្រាប់បញ្ជាក់ការចូលគណនីប៉ុណ្ណោះ។')
SHARE_BUTTON = '📱 Share my phone number / ចែករំលែកលេខទូរស័ព្ទ'
RESTART_MESSAGE = ('This sign-in link has expired. Please go back to the website and tap "Open Telegram" again.\n\n'
                   'តំណចូលគណនីនេះផុតកំណត់ហើយ។ សូមត្រឡប់ទៅគេហទំព័រ ហើយចុច "បើក Telegram" ម្តងទៀត។')
OWN_NUMBER_MESSAGE = ('Please share your own number with the button below.\n\n'
                      'សូមចែករំលែកលេខរបស់អ្នកផ្ទាល់ ដោយប្រើប៊ូតុងខាងក្រោម។')
MISMATCH_MESSAGE = ('This Telegram account uses {phone}, which is different from the number entered on the website. '
                    'Please sign in on the website with {phone}.\n\n'
                    'គណនី Telegram នេះប្រើលេខ {phone} ដែលខុសពីលេខដែលបានបញ្ចូលនៅលើគេហទំព័រ។ '
                    'សូមចូលគណនីនៅលើគេហទំព័រដោយប្រើលេខ {phone}។')


class TelegramError(Exception):
    pass


def api(token, method, http_timeout=15, **params):
    """Call a Bot API method and return its result, raising TelegramError on any failure."""
    request = Request(API_URL.format(token=token, method=method), data=json.dumps(params).encode(),
                      headers={'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=http_timeout) as response:
            result = json.load(response)
    except HTTPError as error:
        try:
            result = json.load(error)
        except ValueError:
            raise TelegramError(f'HTTP {error.code}') from error
    except (OSError, ValueError) as error:
        raise TelegramError(str(error)) from error
    if not result.get('ok'):
        raise TelegramError(result.get('description', 'unknown error'))
    return result['result']


def send_code(app, connection, login_id, chat_id):
    """Create a fresh code for a pending sign-in and send it to the customer's Telegram chat."""
    phone = connection.execute('SELECT phone FROM login_codes WHERE id=?', (login_id,)).fetchone()[0]
    code = new_code()
    api(app.config['TELEGRAM_BOT_TOKEN'], 'sendMessage', chat_id=chat_id, text=CODE_MESSAGE.format(code=code),
        reply_markup={'remove_keyboard': True})
    connection.execute('UPDATE login_codes SET code_hash=?, chat_id=?, attempts=0, expires_at=? WHERE id=?',
                       (hash_code(app.config['SECRET_KEY'], phone, code), chat_id, int(time.time()) + CODE_TTL, login_id))
    connection.commit()


def _reply(app, chat_id, text, **extra):
    api(app.config['TELEGRAM_BOT_TOKEN'], 'sendMessage', chat_id=chat_id, text=text, **extra)


def _latest_pending(connection, condition, value):
    """The newest unexpired sign-in request matching the condition, if it is the newest for its phone."""
    row = connection.execute(f'SELECT * FROM login_codes WHERE {condition}=? AND expires_at>? ORDER BY id DESC LIMIT 1',
                             (value, int(time.time()))).fetchone()
    if row and row['id'] == connection.execute('SELECT max(id) FROM login_codes WHERE phone=?', (row['phone'],)).fetchone()[0]:
        return row
    return None


def handle_update(app, update):
    message = update.get('message') or {}
    chat = message.get('chat') or {}
    if chat.get('type') != 'private':
        return
    chat_id, sender_id = chat['id'], (message.get('from') or {}).get('id')
    with closing(database.connect(app.config)) as connection:
        text = message.get('text', '')
        if text.startswith('/start'):
            start_token = text.partition(' ')[2].strip()
            pending = _latest_pending(connection, 'start_token', start_token) if start_token else None
            if not pending:
                _reply(app, chat_id, RESTART_MESSAGE)
                return
            connection.execute('UPDATE login_codes SET chat_id=? WHERE id=?', (chat_id, pending['id']))
            connection.commit()
            known = connection.execute('SELECT 1 FROM telegram_chats WHERE phone=? AND chat_id=?', (pending['phone'], chat_id)).fetchone()
            if known:
                send_code(app, connection, pending['id'], chat_id)
            else:
                _reply(app, chat_id, SHARE_MESSAGE, reply_markup={
                    'keyboard': [[{'text': SHARE_BUTTON, 'request_contact': True}]], 'one_time_keyboard': True, 'resize_keyboard': True})
        elif message.get('contact'):
            contact = message['contact']
            # A forwarded contact card belongs to someone else; only the sender's own number counts.
            if contact.get('user_id') != sender_id:
                _reply(app, chat_id, OWN_NUMBER_MESSAGE)
                return
            phone = normalize_phone('+' + re.sub(r'\D', '', contact.get('phone_number', '')))
            pending = _latest_pending(connection, 'chat_id', chat_id)
            if not phone or not pending:
                _reply(app, chat_id, RESTART_MESSAGE, reply_markup={'remove_keyboard': True})
                return
            connection.execute('INSERT INTO telegram_chats(phone,chat_id,updated_at) VALUES(?,?,?) '
                               'ON CONFLICT(phone) DO UPDATE SET chat_id=excluded.chat_id, updated_at=excluded.updated_at',
                               (phone, chat_id, int(time.time())))
            connection.commit()
            if phone != pending['phone']:
                _reply(app, chat_id, MISMATCH_MESSAGE.format(phone=phone), reply_markup={'remove_keyboard': True})
                return
            send_code(app, connection, pending['id'], chat_id)


def poll_forever(app, stop_event=None):
    """Long-poll Telegram for messages; works without a public web address."""
    token, offset = app.config['TELEGRAM_BOT_TOKEN'], 0
    while not (stop_event and stop_event.is_set()):
        try:
            updates = api(token, 'getUpdates', http_timeout=40, offset=offset, timeout=30, allowed_updates=['message'])
        except TelegramError as error:
            log.warning('Telegram getUpdates failed: %s', error)
            time.sleep(5)
            continue
        for update in updates:
            offset = update['update_id'] + 1
            try:
                handle_update(app, update)
            except Exception:
                log.exception('Could not handle Telegram update %s', update.get('update_id'))


def webhook_secret(token):
    """Secret Telegram sends with every webhook call, derived from the bot token so no extra setting is needed."""
    return hashlib.sha256(f'webhook:{token}'.encode()).hexdigest()[:48]


def set_webhook(app, base_url):
    """Point the bot at a public HTTPS site (for example the Vercel deployment) instead of polling."""
    token = app.config['TELEGRAM_BOT_TOKEN']
    api(token, 'setWebhook', url=base_url.rstrip('/') + '/telegram/webhook', secret_token=webhook_secret(token),
        allowed_updates=['message'], drop_pending_updates=True)


def bot_username(app):
    """The bot's @username for t.me links, fetched from Telegram once per process when not configured."""
    if not app.config.get('TELEGRAM_BOT_USERNAME'):
        app.config['TELEGRAM_BOT_USERNAME'] = api(app.config['TELEGRAM_BOT_TOKEN'], 'getMe')['username']
    return app.config['TELEGRAM_BOT_USERNAME']


def start_polling(app):
    """Start polling in a background thread. Returns False if the token fails or the live site owns the bot."""
    token = app.config['TELEGRAM_BOT_TOKEN']
    try:
        bot_username(app)
        webhook = api(token, 'getWebhookInfo').get('url')
    except TelegramError as error:
        log.error('Telegram bot token was rejected or Telegram is unreachable: %s', error)
        return False
    if webhook:
        # Polling would require deleting the live site's webhook and break sign-in there.
        log.warning('Telegram bot @%s is connected to %s, so it is not polling here. Use a separate test bot locally.',
                    app.config['TELEGRAM_BOT_USERNAME'], webhook)
        return False
    threading.Thread(target=poll_forever, args=(app,), name='telegram-bot', daemon=True).start()
    log.warning('Telegram bot @%s is running', app.config['TELEGRAM_BOT_USERNAME'])
    return True
