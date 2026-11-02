import functools
import json
import re
import secrets
import sqlite3
from datetime import timedelta
from urllib.parse import urlencode, urlsplit

import click
from flask import Flask, abort, current_app, flash, g, jsonify, redirect, render_template, request, session, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config, ROOT

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)


def db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db


def admin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('admin_id'):
            return redirect(url_for('admin_login'))
        return view(*args, **kwargs)
    return wrapped


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if not app.config.get('SECRET_KEY'):
        key_file = ROOT / '.secret_key'
        if not key_file.exists():
            key_file.write_text(secrets.token_hex(32), encoding='utf-8')
        app.config['SECRET_KEY'] = key_file.read_text(encoding='utf-8').strip()
    app.permanent_session_lifetime = timedelta(minutes=30)
    csrf.init_app(app)
    limiter.init_app(app)
    translations = {lang: json.loads((ROOT / 'translations' / f'{lang}.json').read_text(encoding='utf-8')) for lang in ('en', 'km')}
    dummy_hash = generate_password_hash(secrets.token_hex(24))

    @app.before_request
    def restore_language():
        language = request.cookies.get('language')
        if session.get('language') not in translations:
            session['language'] = language if language in translations else 'en'

    def t(key):
        return translations.get(session.get('language', 'en'), translations['en']).get(key, translations['en'].get(key, key))

    @app.context_processor
    def context():
        return dict(t=t, lang=session.get('language', 'en'), languages={'en': 'English', 'km': 'ខ្មែរ'}, contact_email=app.config['CONTACT_EMAIL'], contact_phone=app.config['CONTACT_PHONE'])

    @app.teardown_appcontext
    def close_db(error=None):
        connection = g.pop('db', None)
        if connection:
            connection.close()

    with app.app_context():
        db().executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL,
                phone TEXT NOT NULL DEFAULT '', subject TEXT NOT NULL, message TEXT NOT NULL,
                language TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')));
            CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS retailers (id INTEGER PRIMARY KEY, name TEXT NOT NULL,
                country TEXT NOT NULL, city TEXT NOT NULL, address TEXT NOT NULL,
                phone TEXT NOT NULL DEFAULT '', email TEXT NOT NULL DEFAULT '', is_demo INTEGER NOT NULL DEFAULT 0);
        ''')
        db().commit()

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self'; font-src 'self'; script-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'"
        if response.mimetype == 'text/html' or request.path.startswith(('/admin', '/set-language', '/api')):
            response.headers['Cache-Control'] = 'no-store'
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

    @app.get('/')
    def index():
        return render_template('index.html', page='home')

    @app.get('/about')
    def about():
        return render_template('about.html', page='about')

    @app.get('/retailers')
    def retailers():
        country = request.args.get('country', '').strip()[:80]
        city = request.args.get('city', '').strip()[:80]
        rows = db().execute("SELECT * FROM retailers WHERE (?='' OR country=?) AND (?='' OR instr(lower(city),lower(?))>0) ORDER BY country,city,name", (country, country, city, city)).fetchall()
        countries = [row[0] for row in db().execute('SELECT DISTINCT country FROM retailers ORDER BY country')]
        return render_template('retailers.html', page='retailers', retailers=rows, countries=countries, country=country, city=city)

    @app.get('/contact')
    def contact():
        return render_template('contact.html', page='contact', values={}, errors={})

    @app.post('/api/contact')
    @limiter.limit('5 per minute;30 per hour')
    def submit_contact():
        data = request.get_json(silent=True) if request.is_json else request.form
        if not isinstance(data, dict) and request.is_json:
            abort(400)
        data = data or {}
        values = {key: str(data.get(key, '')).strip() for key in ('name', 'email', 'phone', 'subject', 'message')}
        errors = {}
        for key, minimum, maximum in [('name', 2, 100), ('subject', 3, 160), ('message', 10, 5000)]:
            if not minimum <= len(values[key]) <= maximum:
                errors[key] = t('error_' + key)
        if len(values['email']) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', values['email']):
            errors['email'] = t('error_email')
        if values['phone'] and not re.fullmatch(r'[+\d ()\-.]{5,30}', values['phone']):
            errors['phone'] = t('error_phone')
        if data.get('website'):
            errors['message'] = t('error_form')
        if errors:
            if request.is_json:
                return jsonify(ok=False, errors=errors), 422
            return render_template('contact.html', page='contact', values=values, errors=errors), 422
        try:
            db().execute('INSERT INTO messages(name,email,phone,subject,message,language) VALUES(?,?,?,?,?,?)', (*values.values(), session.get('language', 'en')))
            db().commit()
        except sqlite3.Error:
            db().rollback()
            app.logger.exception('Contact persistence failed')
            if request.is_json:
                return jsonify(ok=False, message=t('error_save')), 503
            return render_template('contact.html', page='contact', values=values, errors={'form': t('error_save')}), 503
        if request.is_json:
            return jsonify(ok=True, message=t('success')), 201
        flash(t('success'), 'success')
        return redirect(url_for('contact'), code=303)

    @app.get('/set-language/<language>')
    def set_language(language):
        if language not in translations:
            abort(404)
        session['language'] = language
        session.permanent = True
        target = request.args.get('next', '/')
        parts = urlsplit(target)
        if parts.scheme or parts.netloc or not target.startswith('/') or target.startswith('//') or '\\' in target or any(ord(c) < 32 for c in target):
            target = '/'
        response = redirect(target)
        response.set_cookie('language', language, max_age=31536000, httponly=True,
                            secure=app.config['SESSION_COOKIE_SECURE'], samesite='Lax')
        return response

    @app.route('/admin/login', methods=['GET', 'POST'])
    @limiter.limit('10 per minute;50 per hour', methods=['POST'])
    def admin_login():
        error = None
        if request.method == 'POST':
            username = request.form.get('username', '')[:100]
            user = db().execute('SELECT * FROM admins WHERE username=?', (username,)).fetchone()
            # Run a password hash check even when the account does not exist.
            valid = check_password_hash(user['password_hash'] if user else dummy_hash, request.form.get('password', ''))
            if user and valid:
                language = session.get('language', 'en')
                session.clear()
                session.update(admin_id=user['id'], language=language)
                session.permanent = True
                return redirect(url_for('admin'))
            error = t('login_error')
        return render_template('admin_login.html', page='admin', error=error)

    @app.post('/admin/logout')
    @admin_required
    def admin_logout():
        language = session.get('language', 'en')
        session.clear()
        session['language'] = language
        return redirect(url_for('index'))

    @app.get('/admin')
    @admin_required
    def admin():
        status = request.args.get('status', '')
        if status not in ('', 'new', 'read', 'archived'):
            abort(400)
        messages = db().execute("SELECT * FROM messages WHERE (?='' OR status=?) ORDER BY id DESC LIMIT 200", (status, status)).fetchall()
        stats = dict(db().execute('SELECT status,count(*) FROM messages GROUP BY status').fetchall())
        stores = db().execute('SELECT * FROM retailers ORDER BY id DESC').fetchall()
        return render_template('admin.html', page='admin', messages=messages, stats=stats, stores=stores, status=status)

    @app.post('/admin/messages/<int:message_id>/status')
    @admin_required
    def message_status(message_id):
        status = request.form.get('status')
        if status not in ('new', 'read', 'archived'):
            abort(400)
        if not db().execute('UPDATE messages SET status=? WHERE id=?', (status, message_id)).rowcount:
            abort(404)
        db().commit()
        return redirect(url_for('admin'))

    @app.post('/admin/retailers')
    @admin_required
    def save_retailer():
        fields = {key: request.form.get(key, '').strip() for key in ('name', 'country', 'city', 'address', 'phone', 'email')}
        if any(not fields[key] or len(fields[key]) > 200 for key in ('name', 'country', 'city', 'address')) or len(fields['email']) > 254 or (fields['email'] and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', fields['email'])) or (fields['phone'] and not re.fullmatch(r'[+\d ()\-.]{5,30}', fields['phone'])):
            flash(t('error_retailer'), 'error')
        else:
            retailer_id = request.form.get('id')
            if retailer_id:
                if not db().execute('UPDATE retailers SET name=?,country=?,city=?,address=?,phone=?,email=?,is_demo=0 WHERE id=?', (*fields.values(), retailer_id)).rowcount:
                    abort(404)
            else:
                db().execute('INSERT INTO retailers(name,country,city,address,phone,email) VALUES(?,?,?,?,?,?)', tuple(fields.values()))
            db().commit()
            flash(t('saved'), 'success')
        return redirect(url_for('admin') + '#retailer-admin')

    @app.post('/admin/retailers/<int:retailer_id>/delete')
    @admin_required
    def delete_retailer(retailer_id):
        db().execute('DELETE FROM retailers WHERE id=?', (retailer_id,))
        db().commit()
        return redirect(url_for('admin') + '#retailer-admin')

    @app.template_filter('map_url')
    def map_url(value):
        return 'https://www.google.com/maps/search/?' + urlencode({'api': 1, 'query': value})

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        if request.is_json:
            return jsonify(ok=False, message=t('error_csrf')), 400
        return render_template('error.html', page='error', code=400, detail=t('error_csrf')), 400

    for code in (400, 404, 413, 429, 500):
        def error_page(error, code=code):
            if request.is_json:
                return jsonify(ok=False, message=t('error_' + str(code))), code
            return render_template('error.html', page='error', code=code, detail=t('error_' + str(code))), code
        app.register_error_handler(code, error_page)

    @app.cli.command('create-admin')
    @click.option('--username', prompt=True)
    @click.password_option(confirmation_prompt=True)
    def create_admin(username, password):
        if not 3 <= len(username.strip()) <= 100 or len(password) < 12:
            raise click.ClickException('Username must be 3–100 characters; password must be at least 12 characters.')
        if db().execute('SELECT id FROM admins WHERE username=?', (username.strip(),)).fetchone():
            raise click.ClickException('That username already exists.')
        db().execute('INSERT INTO admins(username,password_hash) VALUES(?,?)', (username.strip(), generate_password_hash(password)))
        db().commit()
        click.echo('Administrator created. Sign in at /admin/login.')

    @app.cli.command('seed-demo')
    def seed_demo():
        if not db().execute('SELECT id FROM retailers LIMIT 1').fetchone():
            db().executemany('INSERT INTO retailers(name,country,city,address,is_demo) VALUES(?,?,?,?,1)', [('The Botanical Store · Example', 'Rwanda', 'Kigali', 'Kicukiro, Kigali'), ('The Wellness Edit · Example', 'Rwanda', 'Kigali', 'Kimihurura, Kigali'), ('Green Living · Example', 'Cambodia', 'Phnom Penh', 'BKK1, Phnom Penh')])
            db().commit()
        click.echo('Illustrative retailers added; replace with verified listings before launch.')
    return app


app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5050, debug=False)
