import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    DATABASE = str(ROOT / 'database.db')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
    MAX_CONTENT_LENGTH = 32 * 1024
    WTF_CSRF_TIME_LIMIT = 3600
    RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', 'memory://')
    CONTACT_EMAIL = os.getenv('CONTACT_EMAIL', '')
    CONTACT_PHONE = os.getenv('CONTACT_PHONE', '')
