"""Real HTTP smoke test with Waitress and a disposable SQLite database."""
import http.cookiejar
import re
import secrets
import sqlite3
import sys
import tempfile
import threading
from contextlib import closing
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from waitress import create_server
from werkzeug.security import generate_password_hash


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('img', 'script', 'link'):
            url = attrs.get('src', attrs.get('href', ''))
            if url.startswith('/static/'):
                self.urls.add(url)


def main():
    with tempfile.TemporaryDirectory() as temporary:
        database = str(Path(temporary) / 'http.db')
        application = create_app({'DATABASE': database, 'TESTING': True, 'SECRET_KEY': secrets.token_hex(32), 'RATELIMIT_ENABLED': False})
        password = secrets.token_urlsafe(24)
        with closing(sqlite3.connect(database)) as connection, connection:
            connection.execute('INSERT INTO admins(username,password_hash) VALUES(?,?)', ('smoke-admin', generate_password_hash(password)))
        server = create_server(application, host='127.0.0.1', port=0, threads=2)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.effective_port}'
        opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

        def get(path):
            with opener.open(base + path, timeout=10) as response:
                assert response.status == 200
                return response.read().decode('utf-8')

        def post(path, data):
            with opener.open(base + path, data=urlencode(data).encode(), timeout=10) as response:
                assert response.status == 200
                return response.read().decode('utf-8')

        try:
            parser = Assets()
            for language in ('en', 'km'):
                get('/set-language/' + language)
                for path in ('/', '/about', '/retailers', '/contact', '/admin/login'):
                    html = get(path)
                    assert f'<html lang="{language}">' in html
                    parser.feed(html)
            for path in parser.urls:
                with opener.open(base + path, timeout=10) as response:
                    assert response.status == 200 and response.read()
            get('/set-language/en')
            csrf = re.search(r'name="csrf_token" value="([^"]+)"', get('/contact'))[1]
            html = post('/api/contact', dict(csrf_token=csrf, name='HTTP Smoke Test', email='smoke@example.com', phone='', subject='HTTP verification', message='This is a disposable HTTP integration test.'))
            assert 'Your message has been received' in html
            csrf = re.search(r'name="csrf_token" value="([^"]+)"', get('/admin/login'))[1]
            html = post('/admin/login', dict(csrf_token=csrf, username='smoke-admin', password=password))
            assert 'HTTP Smoke Test' in html
            assert 'HTTP verification' in html
            with closing(sqlite3.connect(database)) as connection, connection:
                assert connection.execute('SELECT count(*) FROM messages').fetchone()[0] == 1
            print(f'HTTP smoke passed: 10 localized pages, {len(parser.urls)} assets, contact save, and admin sign-in/inbox. Test database discarded.')
        finally:
            server.close()
            thread.join(timeout=2)


if __name__ == '__main__':
    main()
