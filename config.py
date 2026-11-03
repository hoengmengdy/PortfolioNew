import os
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
# Vercel sets VERCEL=1 in its build and runtime environment.
ON_VERCEL = bool(os.getenv('VERCEL'))


class Config:
    ON_VERCEL = ON_VERCEL
    SECRET_KEY = os.getenv('SECRET_KEY')
    DATABASE = str(ROOT / 'database.db')
    # Postgres in production (Vercel's Neon integration sets DATABASE_URL); local SQLite file when empty.
    DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL', '')
    # First administrator for hosted sites; created on start-up if that username does not exist yet.
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', '')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')
    BEHIND_PROXY = ON_VERCEL or os.getenv('BEHIND_PROXY', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('COOKIE_SECURE', 'true' if ON_VERCEL else 'false').lower() == 'true'
    MAX_CONTENT_LENGTH = 32 * 1024
    WTF_CSRF_TIME_LIMIT = 3600
    RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', 'memory://')
    CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', '')
    CONTACT_PHONE = os.getenv('CONTACT_PHONE', '069 777 150')
    CONTACT_ADDRESS = os.getenv('CONTACT_ADDRESS', '')
    BUSINESS_HOURS = os.getenv('BUSINESS_HOURS', '')
    FACEBOOK_URL = os.getenv('FACEBOOK_URL', 'https://www.facebook.com/myempressbeauty') if os.getenv('FACEBOOK_URL', 'https://').startswith('https://') else ''
    # Second Facebook page: the LSV Industry company page.
    COMPANY_FACEBOOK_URL = os.getenv('COMPANY_FACEBOOK_URL', 'https://www.facebook.com/lsvindustry') if os.getenv('COMPANY_FACEBOOK_URL', 'https://').startswith('https://') else ''
    # Telegram group (lsvindustrykh) and the LSV Industry account customers can message directly.
    TELEGRAM_URL = os.getenv('TELEGRAM_URL', 'https://t.me/lsvindustrykh') if os.getenv('TELEGRAM_URL', 'https://').startswith('https://') else ''
    TELEGRAM_CHAT_URL = os.getenv('TELEGRAM_CHAT_URL', 'https://t.me/LSVINDUSTRY') if os.getenv('TELEGRAM_CHAT_URL', 'https://').startswith('https://') else ''
    # Google Maps embed (Share -> Embed a map -> the src link) and the place's own Google Maps link.
    MAP_EMBED_URL = os.getenv('MAP_EMBED_URL', 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d730.3013961561218!2d104.85608354954493!3d11.58680000000001!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x31095151b1b0b307%3A0x40a694e229dd62d8!2sLSV%20Industry%20-%20OKA!5e1!3m2!1skm!2skh!4v1793693664874!5m2!1skm!2skh')
    MAP_EMBED_URL = MAP_EMBED_URL if MAP_EMBED_URL.startswith('https://www.google.com/maps/embed?') else ''
    MAP_URL = os.getenv('MAP_URL', 'https://maps.google.com/?cid=4658574563647251160')
    MAP_NAME = os.getenv('MAP_NAME', 'LSV Industry - OKA')
    INSTAGRAM_URL = os.getenv('INSTAGRAM_URL', '') if os.getenv('INSTAGRAM_URL', '').startswith('https://') else ''
    # Free option: a bot from @BotFather sends sign-in codes. Takes priority over the Gateway when set.
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    # Filled in automatically from Telegram when the bot starts.
    TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME', '').lstrip('@')
    # Paid option: codes sent with the Telegram Gateway API (https://core.telegram.org/gateway).
    TELEGRAM_GATEWAY_TOKEN = os.getenv('TELEGRAM_GATEWAY_TOKEN', '')
    # Local testing only: print codes to the server log instead of sending them.
    TELEGRAM_DEV_MODE = os.getenv('TELEGRAM_DEV_MODE', 'false').lower() == 'true'
    # ABA PayWay (KHQR, ABA PAY, cards). Shown at checkout when merchant ID and API key are set.
    PAYWAY_MERCHANT_ID = os.getenv('PAYWAY_MERCHANT_ID', '')
    PAYWAY_API_KEY = os.getenv('PAYWAY_API_KEY', '')
    # Sandbox by default; use https://checkout.payway.com.kh for live payments.
    # Only scheme and host are kept, so the portal's "API Url" can be pasted with or without its path.
    PAYWAY_BASE_URL = '{0.scheme}://{0.netloc}'.format(urlsplit(os.getenv('PAYWAY_BASE_URL') or 'https://checkout-sandbox.payway.com.kh'))
    PAYWAY_CURRENCY = os.getenv('PAYWAY_CURRENCY', 'USD')
    # Empty shows every method enabled on your PayWay profile; or abapay_khqr, cards, ...
    PAYWAY_PAYMENT_OPTION = os.getenv('PAYWAY_PAYMENT_OPTION', '')
    CURRENCY_SYMBOL = os.getenv('CURRENCY_SYMBOL', '$')
    DELIVERY_FEE_CENTS = int(Decimal(os.getenv('DELIVERY_FEE', '0') or '0') * 100)
    # Bank transfer / KHQR is offered at checkout only when an account number is set.
    PAYMENT_BANK_NAME = os.getenv('PAYMENT_BANK_NAME', '')
    PAYMENT_ACCOUNT_NAME = os.getenv('PAYMENT_ACCOUNT_NAME', '')
    PAYMENT_ACCOUNT_NUMBER = os.getenv('PAYMENT_ACCOUNT_NUMBER', '')
