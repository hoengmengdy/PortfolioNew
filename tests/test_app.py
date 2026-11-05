import json
import os
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

import database
from app import create_app

# Set TEST_DATABASE_URL to run the whole suite against Postgres instead of a temporary SQLite file.
TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL', '')


@contextmanager
def connect_db(app):
    """A committed connection to the test database whose rows compare equal to plain tuples."""
    connection = database.connect(app.config)
    if isinstance(connection, sqlite3.Connection):
        connection.row_factory = None
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


@pytest.fixture
def app(tmp_path):
    if TEST_DATABASE_URL:
        import psycopg
        with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
            connection.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public')
    application = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret', 'DATABASE': str(tmp_path / 'test.db'), 'DATABASE_URL': TEST_DATABASE_URL, 'RATELIMIT_ENABLED': False, 'DELIVERY_FEE_CENTS': 150, 'PAYMENT_BANK_NAME': 'Test Bank', 'PAYMENT_ACCOUNT_NUMBER': '000 111 222',
                              # Never use real Telegram or PayWay credentials from a developer's .env in tests.
                              'TELEGRAM_BOT_TOKEN': '', 'TELEGRAM_GATEWAY_TOKEN': '', 'TELEGRAM_DEV_MODE': False, 'PAYWAY_MERCHANT_ID': '', 'PAYWAY_API_KEY': '', 'ADMIN_USERNAME': '', 'ADMIN_PASSWORD': '', 'ON_VERCEL': False})
    with connect_db(application) as connection:
        connection.execute('INSERT INTO admins(username,password_hash) VALUES(?,?)', ('owner', generate_password_hash('long-test-password')))
        connection.executemany('INSERT INTO retailers(name,country,city,address) VALUES(?,?,?,?)', [('Kigali Store', 'Rwanda', 'Kigali', 'Kicukiro'), ('Phnom Store', 'Cambodia', 'Phnom Penh', 'BKK1')])
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def token(client, path='/contact'):
    response = client.get(path)
    return re.search(r'name="csrf_token" value="([^"]+)"', response.text)[1]


def login(client):
    return client.post('/admin/login', data={'csrf_token': token(client, '/admin/login'), 'username': 'owner', 'password': 'long-test-password'})


def payload(client):
    return dict(csrf_token=token(client), name='Test Visitor', email='visitor@example.com', phone='+250 123 456 789', subject='Retail partnership', message='Please send more information about your collection.')


@pytest.mark.parametrize('path', ['/', '/herbs', '/about', '/retailers', '/contact', '/shop', '/cart', '/admin/login'])
@pytest.mark.parametrize('language', ['en', 'km'])
def test_all_pages_and_languages(client, path, language):
    response = client.get(f'/set-language/{language}?next={path}', follow_redirects=True)
    assert response.status_code == 200
    assert f'<html lang="{language}">' in response.text
    assert 'name="description"' in response.text
    assert 'Content-Security-Policy' in response.headers
    assert response.headers['Cache-Control'] == 'no-store'


@pytest.mark.parametrize('slug', ['napa-cabbage', 'rau-d', 'ingredient-x', 'ingredient-y', 'aloe-vera', 'centella-asiatica', 'turmeric', 'green-tea'])
def test_herb_detail_pages(client, slug):
    response = client.get(f'/herbs/{slug}')
    assert response.status_code == 200
    assert f'images/herbs/{slug}.svg' in response.text
    assert 'id="herb-heading"' in response.text


@pytest.mark.parametrize('slug', ['unknown', 'napa_cabbage', 'title'])
def test_unknown_herb_is_not_found(client, slug):
    assert client.get(f'/herbs/{slug}').status_code == 404


def test_herb_cards_link_to_detail_pages_and_nav_lists_herbs(client):
    page = client.get('/herbs').text
    assert 'href="/herbs/napa-cabbage"' in page and 'href="/herbs/green-tea"' in page
    assert 'href="/herbs/aloe-vera"' in client.get('/').text
    nav = re.search(r'<nav id="navigation".*?</nav>', page, re.S)[0]
    assert nav.index('href="/about"') < nav.index('href="/herbs"') < nav.index('href="/contact"')
    assert 'nav-submenu' not in nav


def test_account_link_moved_from_header_to_footer(client):
    page = client.get('/').text
    header = re.search(r'<header.*?</header>', page, re.S)[0]
    footer = re.search(r'<footer.*?</footer>', page, re.S)[0]
    assert '/account' not in header
    assert 'href="/account/login"' in footer


def test_homepage_video_highlights(client):
    page = client.get('/').text
    for n in range(1, 6):
        assert f'src="/videos/koc-{n}.mp4"' in page
        assert f'images/videos/koc-{n}.webp' in page
    response = client.get('/videos/koc-1.mp4', headers={'Range': 'bytes=0-99'})
    assert response.status_code == 206 and response.mimetype == 'video/mp4' and len(response.data) == 100
    assert client.get('/videos/missing.mp4').status_code == 404

def test_language_remembered_and_redirects_safe(client):
    response = client.get('/set-language/km?next=https://evil.example')
    assert response.location == '/'
    assert 'Max-Age=31536000' in response.headers.getlist('Set-Cookie')[0]
    with client.session_transaction() as session:
        session.clear()
    assert '<html lang="km">' in client.get('/about').text
    for target in ['//evil.example', '/\\evil.example', 'javascript:alert(1)']:
        assert client.get('/set-language/en', query_string={'next': target}).location == '/'
    assert client.get('/set-language/fr').status_code == 404


def test_header_and_retired_language(client):
    client.set_cookie('language', 'rw')
    with client.session_transaction() as session:
        session['language'] = 'rw'
    response = client.get('/')
    assert response.status_code == 200
    assert '<html lang="en">' in response.text
    assert 'class="announcement"' not in response.text
    assert 'class="nav-cta"' not in response.text
    assert '/set-language/rw' not in response.text
    assert '/set-language/en' in response.text
    assert '/set-language/km' in response.text
    assert client.get('/set-language/rw').status_code == 404


def test_contact_saved_and_admin_view_escapes_html(client, app):
    data = payload(client)
    data['message'] = '<script>alert("xss")</script> This is a test inquiry.'
    response = client.post('/api/contact', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert 'Your message has been received' in response.text
    with connect_db(app) as connection:
        row = connection.execute('SELECT name,email,message,status FROM messages').fetchone()
    assert row == ('Test Visitor', 'visitor@example.com', data['message'], 'new')
    assert login(client).status_code == 302
    html = client.get('/admin').text
    assert '&lt;script&gt;' in html
    assert '<script>alert(' not in html


def test_json_api_validation_csrf_and_persistence(client, app):
    assert client.post('/api/contact', json={'name': 'Test'}).status_code == 400
    data = payload(client)
    csrf_token = data.pop('csrf_token')
    response = client.post('/api/contact', json=data, headers={'X-CSRFToken': csrf_token})
    assert response.status_code == 201 and response.json['ok']
    data['email'] = 'bad-email'
    data['message'] = 'short'
    response = client.post('/api/contact', json=data, headers={'X-CSRFToken': csrf_token})
    assert response.status_code == 422
    assert set(response.json['errors']) == {'email', 'message'}
    with connect_db(app) as connection:
        assert connection.execute('SELECT count(*) FROM messages').fetchone()[0] == 1


def test_form_error_preserves_input_and_honeypot(client):
    data = payload(client)
    data.update(email='wrong', name='A', phone='not-a-phone', message='short', subject='x')
    response = client.post('/api/contact', data=data)
    assert response.status_code == 422
    assert 'value="wrong"' in response.text
    assert 'aria-invalid="true"' in response.text
    data = payload(client)
    data['website'] = 'spam'
    assert client.post('/api/contact', data=data).status_code == 422


def test_admin_access_status_and_logout(client, app):
    assert client.get('/admin').status_code == 302
    assert client.post('/admin/retailers', data={'csrf_token': token(client)}).status_code == 302
    assert client.post('/admin/login', data={'csrf_token': token(client, '/admin/login'), 'username': "' OR 1=1--", 'password': 'bad'}).status_code == 200
    assert client.get('/admin').status_code == 302
    client.post('/api/contact', data=payload(client))
    login(client)
    assert client.get('/admin').status_code == 200
    assert client.post('/admin/messages/1/status', data={'csrf_token': token(client, '/admin'), 'status': 'read'}).status_code == 302
    with connect_db(app) as connection:
        assert connection.execute('SELECT status FROM messages WHERE id=1').fetchone()[0] == 'read'
    assert client.post('/admin/messages/1/status', data={'csrf_token': token(client, '/admin'), 'status': 'invalid'}).status_code == 400
    assert client.post('/admin/logout', data={'csrf_token': token(client, '/admin')}).status_code == 302
    assert client.get('/admin').status_code == 302


def test_retailer_search_and_admin_crud(client, app):
    response = client.get('/retailers?city=kig')
    assert 'Kigali Store' in response.text and 'Phnom Store' not in response.text
    assert 'No retailers found' in client.get('/retailers?city=unknown').text
    assert client.get('/retailers?city=%27%20OR%201%3D1--').status_code == 200
    login(client)
    retailer = dict(csrf_token=token(client, '/admin'), name='New Store', country='Rwanda', city='Huye', address='Main street', phone='', email='store@example.com')
    assert client.post('/admin/retailers', data=retailer).status_code == 302
    assert 'New Store' in client.get('/retailers?city=Huye').text
    with connect_db(app) as connection:
        retailer_id = connection.execute('SELECT id FROM retailers WHERE name=?', ('New Store',)).fetchone()[0]
    retailer.update(id=str(retailer_id), name='Updated Store')
    assert client.post('/admin/retailers', data=retailer).status_code == 302
    assert 'Updated Store' in client.get('/retailers?city=Huye').text
    assert client.post(f'/admin/retailers/{retailer_id}/delete', data={'csrf_token': token(client, '/admin')}).status_code == 302
    assert 'Updated Store' not in client.get('/retailers').text


def test_admin_cli(app):
    runner = app.test_cli_runner()
    assert runner.invoke(args=['create-admin', '--username', 'new-owner'], input='short\nshort\n').exit_code != 0
    assert runner.invoke(args=['create-admin', '--username', 'new-owner'], input='a-long-password-123\na-long-password-123\n').exit_code == 0
    assert runner.invoke(args=['create-admin', '--username', 'new-owner'], input='a-long-password-123\na-long-password-123\n').exit_code != 0


def test_rate_limit_and_csrf_on_admin(app):
    from app import limiter
    app.config['RATELIMIT_ENABLED'] = True
    limiter.enabled = True
    limiter.reset()
    client = app.test_client()
    assert client.post('/admin/login', data={'username': 'owner'}).status_code == 400
    data = payload(client)
    statuses = [client.post('/api/contact', data=data).status_code for _ in range(6)]
    assert statuses[:5] == [303] * 5
    assert statuses[5] == 429


def test_translation_catalogs_are_complete(client):
    root = Path(__file__).resolve().parents[1]
    catalogs = [json.loads((root / 'translations' / f'{lang}.json').read_text(encoding='utf-8')) for lang in ('en', 'km')]
    assert all(set(catalog) == set(catalogs[0]) for catalog in catalogs)
    assert all(all(value.strip() for value in catalog.values()) for catalog in catalogs)
    # Catch encoding loss when regenerating Khmer text on Windows.
    assert all('???' not in value for value in catalogs[1].values())
    for template in (root / 'templates').glob('*.html'):
        for key in re.findall(r"\bt\('([a-z_]+)'\)", template.read_text(encoding='utf-8')):
            assert key in catalogs[0], (template.name, key)


def test_contact_map_is_allowed_only_from_google(client, app):
    response = client.get('/contact')
    assert 'src="https://www.google.com/maps/embed?' in response.text and 'maps.google.com/?cid=' in response.text
    assert 'frame-src https://www.google.com;' in response.headers['Content-Security-Policy']
    app.config['MAP_EMBED_URL'] = ''
    response = client.get('/contact')
    assert '<iframe' not in response.text and "frame-src 'none'" in response.headers['Content-Security-Policy']
