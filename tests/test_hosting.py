"""Settings used when the site runs on a host such as Vercel."""
import pytest
from werkzeug.security import check_password_hash

import app as app_module
from test_app import TEST_DATABASE_URL, app, client, connect_db, token  # noqa: F401  (pytest fixtures)


def make_app(tmp_path, **config):
    base = {'TESTING': True, 'SECRET_KEY': 'test-secret', 'DATABASE': str(tmp_path / 'hosted.db'), 'DATABASE_URL': TEST_DATABASE_URL,
            'TELEGRAM_BOT_TOKEN': '', 'PAYWAY_MERCHANT_ID': '', 'ADMIN_USERNAME': '', 'ADMIN_PASSWORD': '', 'ON_VERCEL': False}
    return app_module.create_app({**base, **config})


def test_first_admin_from_environment(app, tmp_path):
    hosted = make_app(tmp_path, ADMIN_USERNAME='owner2', ADMIN_PASSWORD='a-long-admin-password')
    with connect_db(hosted) as connection:
        stored = connection.execute("SELECT password_hash FROM admins WHERE username='owner2'").fetchone()[0]
    assert check_password_hash(stored, 'a-long-admin-password')
    # Restarting with the same settings does not duplicate or overwrite the account.
    make_app(tmp_path, ADMIN_USERNAME='owner2', ADMIN_PASSWORD='another-long-password')
    with connect_db(hosted) as connection:
        assert connection.execute("SELECT count(*) FROM admins WHERE username='owner2'").fetchone()[0] == 1
        assert connection.execute("SELECT password_hash FROM admins WHERE username='owner2'").fetchone()[0] == stored
    make_app(tmp_path, ADMIN_USERNAME='x', ADMIN_PASSWORD='short')
    with connect_db(hosted) as connection:
        assert connection.execute("SELECT count(*) FROM admins WHERE username='x'").fetchone()[0] == 0


def test_vercel_needs_a_database_and_secret(tmp_path):
    with pytest.raises(RuntimeError, match='DATABASE_URL'):
        make_app(tmp_path, ON_VERCEL=True, DATABASE_URL='')


def test_proxy_headers_give_https_links(tmp_path):
    hosted = make_app(tmp_path, BEHIND_PROXY=True)
    client = hosted.test_client()
    headers = {'X-Forwarded-Proto': 'https', 'X-Forwarded-Host': 'empresscambodia.vercel.app'}
    page = client.get('/', headers=headers).text
    assert 'https://empresscambodia.vercel.app/static/images/soap-hero-small.webp' in page
