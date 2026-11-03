"""Phone-number and sign-in code helpers shared by the website and the Telegram bot."""
import hashlib
import hmac
import re
import secrets

CODE_TTL = 300
CODE_MAX_ATTEMPTS = 5
# Time a customer has to open the bot and share their number before the sign-in request lapses.
LINK_TTL = 900


def normalize_phone(value):
    """Return a phone number in E.164 form, treating local numbers such as 012 345 678 as Cambodian."""
    number = re.sub(r'[\s\-().]', '', value or '')
    if number.startswith('00'):
        number = '+' + number[2:]
    elif number.startswith('0'):
        number = '+855' + number[1:]
    elif number.startswith('855'):
        number = '+' + number
    return number if re.fullmatch(r'\+[1-9]\d{7,14}', number) else None


def new_code():
    return f'{secrets.randbelow(10 ** 6):06d}'


def hash_code(secret_key, phone, code):
    """Keyed hash of a code, so the database never holds codes that could be used directly."""
    return hmac.new(secret_key.encode(), f'{phone}:{code}'.encode(), hashlib.sha256).hexdigest()
