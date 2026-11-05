import functools
import hmac
import io
import json
import re
import secrets
import time
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

import click
from flask import Flask, Response, abort, current_app, flash, g, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect, CSRFError
from PIL import Image, ImageOps
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash

import database
import locations
import payway
import telegram_bot
from config import Config, ROOT
from phone_codes import CODE_MAX_ATTEMPTS, CODE_TTL, LINK_TTL, hash_code, new_code, normalize_phone

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

EMAIL_RE = r'[^\s@]+@[^\s@]+\.[^\s@]+'
PHONE_RE = r'[+\d ()\-.]{5,30}'
ORDER_STATUSES = ('pending', 'confirmed', 'shipped', 'completed', 'cancelled')
PAYMENT_STATUSES = ('unpaid', 'submitted', 'paid', 'refunded')
MAX_QUANTITY = 20
LOW_STOCK = 5
# Product photos uploaded in the admin are stored in the database (hosted file systems are read-only).
PHOTO_PREFIX = 'uploads/'
MAX_PHOTO_BYTES = 4 * 1024 * 1024  # Vercel rejects request bodies above 4.5 MB.
PHOTO_SIZE = 1600
# One-tap order buttons in the admin: new order status and/or payment status.
ORDER_ACTIONS = {'confirm': ('confirmed', None), 'ship': ('shipped', None), 'complete': ('completed', None),
                 'paid': (None, 'paid'), 'cancel': ('cancelled', None), 'reopen': ('pending', None)}
TELEGRAM_GATEWAY_URL = 'https://gatewayapi.telegram.org/sendVerificationMessage'


def send_telegram_code(phone, code):
    """Deliver a login code with the Telegram Gateway API. Returns True when Telegram accepted it."""
    config = current_app.config
    if not config['TELEGRAM_GATEWAY_TOKEN']:
        if config['TELEGRAM_DEV_MODE']:
            current_app.logger.warning('TELEGRAM_DEV_MODE: login code for %s is %s', phone, code)
            return True
        current_app.logger.error('TELEGRAM_GATEWAY_TOKEN is not set; cannot send login codes')
        return False
    request_body = json.dumps({'phone_number': phone, 'code': code, 'ttl': CODE_TTL}).encode()
    gateway_request = Request(TELEGRAM_GATEWAY_URL, data=request_body, headers={
        'Authorization': 'Bearer ' + config['TELEGRAM_GATEWAY_TOKEN'], 'Content-Type': 'application/json'})
    try:
        with urlopen(gateway_request, timeout=10) as response:
            result = json.load(response)
    except (OSError, ValueError):
        current_app.logger.exception('Telegram Gateway request failed')
        return False
    if not result.get('ok'):
        current_app.logger.warning('Telegram Gateway refused the code: %s', result.get('error'))
        return False
    return True


def safe_target(target, default='/'):
    """Allow only local, absolute-path redirect targets."""
    target = target or ''
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or not target.startswith('/') or target.startswith('//') or '\\' in target or any(ord(c) < 32 for c in target):
        return default
    return target


def parse_money(value):
    """Convert a decimal string such as '12.50' to integer cents, or None."""
    try:
        amount = Decimal(str(value).strip())
    except InvalidOperation:
        return None
    if not amount.is_finite() or not 0 <= amount <= 100000 or amount.as_tuple().exponent < -2:
        return None
    return int(amount * 100)


def webp_photo(upload):
    """Return an uploaded JPEG, PNG or WebP as a resized WebP, or None when it is not a usable picture."""
    data = upload.read(MAX_PHOTO_BYTES + 1)
    if not data or len(data) > MAX_PHOTO_BYTES:
        return None
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in ('JPEG', 'PNG', 'WEBP') or image.width * image.height > 40_000_000:
                return None
            image = ImageOps.exif_transpose(image)
            image = image.convert('RGBA' if image.mode in ('RGBA', 'LA', 'P') else 'RGB')
            image.thumbnail((PHOTO_SIZE, PHOTO_SIZE))
            output = io.BytesIO()
            image.save(output, 'WEBP', quality=84, method=4)
            return output.getvalue()
    except (OSError, ValueError, Image.DecompressionBombError):
        return None


def db():
    if 'db' not in g:
        started = time.perf_counter()
        g.db = database.connect(current_app.config, reuse=True)
        g.db_ms = (time.perf_counter() - started) * 1000
    return g.db


def admin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('admin_id'):
            return redirect(url_for('admin_login'))
        return view(*args, **kwargs)
    return wrapped


# Ingredients with a card and a detail page; each needs herb_<key>_* translations and an images/herbs SVG.
NATURAL_HERBS = ('napa_cabbage', 'rau_d', 'ingredient_x', 'ingredient_y')
ACTIVE_INGREDIENTS = ('aloe_vera', 'centella_asiatica', 'turmeric', 'green_tea')
# Herbs with a picture in another format than the usual SVG.
HERB_PICTURES = {'ingredient_x': 'ingredient-x.webp'}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if not app.config.get('SECRET_KEY'):
        key_file = ROOT / '.secret_key'
        try:
            if not key_file.exists():
                key_file.write_text(secrets.token_hex(32), encoding='utf-8')
            app.config['SECRET_KEY'] = key_file.read_text(encoding='utf-8').strip()
        except OSError as error:
            # Hosts such as Vercel have a read-only file system: the key must come from the environment.
            raise RuntimeError('Set the SECRET_KEY environment variable (a long random value).') from error
    if app.config['ON_VERCEL'] and not app.config['DATABASE_URL']:
        raise RuntimeError('On Vercel, connect a Postgres database (Storage tab) so DATABASE_URL is set; files cannot be saved there.')
    if app.config['BEHIND_PROXY']:
        # Vercel terminates HTTPS and forwards the original scheme and host, needed for correct external URLs.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    app.permanent_session_lifetime = timedelta(minutes=30)

    @app.before_request
    def allow_photo_upload():
        # Registered before CSRF, which reads the form: only the product form may exceed the small default body limit.
        if request.endpoint == 'save_product':
            request.max_content_length = MAX_PHOTO_BYTES + 64 * 1024

    csrf.init_app(app)
    limiter.init_app(app)
    translations = {lang: json.loads((ROOT / 'translations' / f'{lang}.json').read_text(encoding='utf-8')) for lang in ('en', 'km')}
    dummy_hash = generate_password_hash(secrets.token_hex(24))

    @app.before_request
    def restore_language():
        g.started = time.perf_counter()
        # Static files must not touch the session: a Set-Cookie header would stop the CDN from caching them.
        if request.endpoint in ('static', 'product_photo'):
            return
        language = request.cookies.get('language')
        if session.get('language') not in translations:
            session['language'] = language if language in translations else 'en'

    def t(key):
        return translations.get(session.get('language', 'en'), translations['en']).get(key, translations['en'].get(key, key))

    def product_image_url(image):
        if image.startswith(PHOTO_PREFIX):
            return url_for('product_photo', photo_id=int(image[len(PHOTO_PREFIX):].removesuffix('.webp')))
        return url_for('static', filename='images/' + image)

    def herb_image(slug):
        return 'images/herbs/' + HERB_PICTURES.get(slug, slug.replace('_', '-') + '.svg')

    def localized(row, field):
        return (session.get('language') == 'km' and row[field + '_km']) or row[field]

    def payment_methods():
        # Cash on delivery is no longer offered; older 'cod' orders still display and complete as before.
        methods = ['payway'] if payway.enabled(app.config) else []
        if app.config['PAYMENT_ACCOUNT_NUMBER']:
            methods.append('bank')
        return tuple(methods)

    def current_customer():
        if 'customer' not in g:
            customer_id = session.get('customer_id')
            g.customer = db().execute('SELECT * FROM customers WHERE id=?', (customer_id,)).fetchone() if customer_id else None
        return g.customer

    def customer_required(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            if not current_customer():
                return redirect(url_for('account_login', next=request.path))
            return view(*args, **kwargs)
        return wrapped

    @app.context_processor
    def context():
        cart_count = sum(session.get('cart', {}).values())
        return dict(t=t, lang=session.get('language', 'en'), languages={'en': 'English', 'km': 'ខ្មែរ'}, contact_email=app.config['CONTACT_EMAIL'], contact_phone=app.config['CONTACT_PHONE'], contact_phone_link=normalize_phone(app.config['CONTACT_PHONE']) or app.config['CONTACT_PHONE'].replace(' ', ''), localized=localized, product_image_url=product_image_url, herb_image=herb_image, cart_count=cart_count, customer=current_customer())

    @app.teardown_appcontext
    def close_db(error=None):
        connection = g.pop('db', None)
        if connection:
            # Postgres connections are kept for the next request on this thread; SQLite files are cheap to reopen.
            connection.release() if database.is_postgres(connection) else connection.close()

    with app.app_context():
        database.create_schema(db())
        db().execute('DELETE FROM login_codes WHERE created_at < ?', (int(time.time()) - 86400,))
        # Starter catalogue built from the concept collection; prices are examples to replace in the admin dashboard.
        if not db().execute('SELECT id FROM products LIMIT 1').fetchone():
            en, km = translations['en'], translations['km']
            db().executemany('INSERT INTO products(name,name_km,description,description_km,price_cents,stock,image) VALUES(?,?,?,?,?,?,?)', [
                (en[slug + '_name'], km[slug + '_name'], en[slug + '_description'], km[slug + '_description'], price, 25, image)
                for slug, price, image in [('serum', 1800, 'hero.webp'), ('cleanser', 950, 'soap-hero.webp'), ('cream', 2200, 'collection-original.webp')]])
        # Hosted sites have no terminal for `flask create-admin`, so the first admin can come from the environment.
        username, password = app.config['ADMIN_USERNAME'].strip(), app.config['ADMIN_PASSWORD']
        if username and password:
            if not 3 <= len(username) <= 100 or len(password) < 12:
                app.logger.error('ADMIN_USERNAME must be 3-100 characters and ADMIN_PASSWORD at least 12; no admin was created.')
            elif not db().execute('SELECT id FROM admins WHERE username=?', (username,)).fetchone():
                db().execute('INSERT INTO admins(username,password_hash) VALUES(?,?) ON CONFLICT(username) DO NOTHING',
                             (username, generate_password_hash(password)))
        db().commit()
    product_images = sorted(path.name for path in (ROOT / 'static' / 'images').glob('*.webp') if '-small' not in path.name)

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # The PayWay checkout form is posted from our page, so its origin must be an allowed form target.
        form_action = "'self' " + app.config['PAYWAY_BASE_URL'].rstrip('/') if payway.enabled(app.config) else "'self'"
        # The contact page embeds a Google Maps frame.
        frame_src = 'https://www.google.com' if app.config['MAP_EMBED_URL'] else "'none'"
        response.headers['Content-Security-Policy'] = f"default-src 'self'; img-src 'self' data:; style-src 'self'; font-src 'self'; script-src 'self'; frame-src {frame_src}; base-uri 'self'; form-action {form_action}; frame-ancestors 'none'; object-src 'none'"
        if request.endpoint == 'product_photo' and response.status_code == 200:
            # A photo id always points at the same bytes; a new upload gets a new id.
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        elif request.endpoint == 'static' and response.status_code in (200, 304):
            # Versioned files (?v=) never change; others may be cached for a day by browsers and a week by the CDN.
            response.headers['Cache-Control'] = ('public, max-age=31536000, immutable' if request.args.get('v')
                                                 else 'public, max-age=86400, s-maxage=604800, stale-while-revalidate=86400')
        elif response.mimetype == 'text/html' or request.path.startswith(('/admin', '/set-language', '/api')):
            response.headers['Cache-Control'] = 'no-store'
        if 'started' in g:
            timing = f"app;dur={(time.perf_counter() - g.started) * 1000:.0f}"
            if 'db_ms' in g:
                timing += f", db-connect;dur={g.db_ms:.0f}"
            response.headers['Server-Timing'] = timing
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

    @app.get('/uploads/<int:photo_id>.webp')
    def product_photo(photo_id):
        row = db().execute('SELECT data FROM product_photos WHERE id=?', (photo_id,)).fetchone()
        if not row:
            abort(404)
        return Response(bytes(row['data']), mimetype='image/webp')

    @app.get('/')
    def index():
        # Products come from the shop, so pictures and text changed in the admin appear here too.
        products = db().execute('SELECT * FROM products WHERE active=1 ORDER BY id DESC').fetchall()
        # Best sellers are real order counts; the section stays hidden until at least two products have sold.
        sold = db().execute("SELECT oi.product_id, SUM(oi.quantity) AS total FROM order_items oi JOIN orders o ON o.id=oi.order_id "
                            "WHERE oi.product_id IS NOT NULL AND o.status<>'cancelled' GROUP BY oi.product_id ORDER BY total DESC, oi.product_id LIMIT 3").fetchall()
        by_id = {product['id']: product for product in products}
        best_sellers = [by_id[row['product_id']] for row in sold if row['product_id'] in by_id]
        best_sellers = best_sellers if len(best_sellers) >= 2 else []
        new_arrivals = [product for product in products if product not in best_sellers][:3]
        return render_template('index.html', page='home', best_sellers=best_sellers, new_arrivals=new_arrivals, active_ingredients=ACTIVE_INGREDIENTS, payment_methods=payment_methods())

    @app.get('/videos/<name>')
    def video(name):
        # On Vercel the CDN answers these from public/videos first (functions cannot send files this large).
        return send_from_directory(Path(app.root_path) / 'public' / 'videos', name, mimetype='video/mp4', conditional=True)

    @app.get('/herbs')
    def herbs():
        return render_template('herbs.html', page='herbs', natural_herbs=NATURAL_HERBS, active_ingredients=ACTIVE_INGREDIENTS)

    @app.get('/herbs/<slug>')
    def herb_detail(slug):
        # URLs use hyphens (napa-cabbage); translation keys use underscores (napa_cabbage).
        herb = slug.replace('-', '_')
        group = next((group for group in (NATURAL_HERBS, ACTIVE_INGREDIENTS) if herb in group), None)
        if group is None or '_' in slug:
            abort(404)
        others = [other for other in group if other != herb]
        return render_template('herb_detail.html', page='herbs', herb=herb, others=others)

    @app.get('/about')
    def about():
        return render_template('about.html', page='about')

    @app.get('/retailers')
    def retailers():
        city = request.args.get('city', '').strip()[:80]
        rows = db().execute("SELECT * FROM retailers WHERE (?='' OR lower(city) LIKE '%' || lower(?) || '%') ORDER BY country,city,name", (city, city)).fetchall()
        return render_template('retailers.html', page='retailers', retailers=rows, city=city)

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
        if len(values['email']) > 254 or not re.fullmatch(EMAIL_RE, values['email']):
            errors['email'] = t('error_email')
        if values['phone'] and not re.fullmatch(PHONE_RE, values['phone']):
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
        except database.ERRORS:
            db().rollback()
            app.logger.exception('Contact persistence failed')
            if request.is_json:
                return jsonify(ok=False, message=t('error_save')), 503
            return render_template('contact.html', page='contact', values=values, errors={'form': t('error_save')}), 503
        if request.is_json:
            return jsonify(ok=True, message=t('success')), 201
        flash(t('success'), 'success')
        return redirect(url_for('contact'), code=303)

    def load_cart():
        """Return (items, subtotal) for the session cart, dropping products that are hidden or deleted."""
        cart = session.get('cart', {})
        rows = db().execute(f"SELECT * FROM products WHERE active=1 AND id IN ({','.join('?' * len(cart))})", [int(key) for key in cart]).fetchall() if cart else []
        items = [dict(product=row, quantity=cart[str(row['id'])], line_cents=row['price_cents'] * cart[str(row['id'])]) for row in rows]
        if len(items) != len(cart):
            session['cart'] = {str(item['product']['id']): item['quantity'] for item in items}
        return items, sum(item['line_cents'] for item in items)

    @app.get('/shop')
    def shop():
        q = request.args.get('q', '').strip()[:80]
        products = db().execute("SELECT * FROM products WHERE active=1 AND (?='' OR lower(name) LIKE '%' || lower(?) || '%' OR name_km LIKE '%' || ? || '%' "
                                "OR lower(description) LIKE '%' || lower(?) || '%' OR description_km LIKE '%' || ? || '%') ORDER BY id", (q, q, q, q, q)).fetchall()
        return render_template('shop.html', page='shop', products=products, q=q)

    @app.get('/shop/<int:product_id>')
    def product_detail(product_id):
        product = db().execute('SELECT * FROM products WHERE id=? AND active=1', (product_id,)).fetchone()
        if not product:
            abort(404)
        related = db().execute('SELECT * FROM products WHERE active=1 AND id<>? ORDER BY id LIMIT 4', (product_id,)).fetchall()
        return render_template('product.html', page='shop', product=product, related=related,
                               custom_title=localized(product, 'name'), page_description=localized(product, 'description'))

    @app.post('/cart/add')
    def cart_add():
        product = db().execute('SELECT * FROM products WHERE id=? AND active=1', (request.form.get('product_id', type=int),)).fetchone()
        if not product:
            abort(404)
        quantity = max(1, min(request.form.get('quantity', 1, type=int) or 1, MAX_QUANTITY))
        cart = session.get('cart', {})
        key = str(product['id'])
        total = min(cart.get(key, 0) + quantity, product['stock'], MAX_QUANTITY)
        if total <= cart.get(key, 0):
            flash(t('out_of_stock'), 'error')
        else:
            cart[key] = total
            session['cart'] = cart
            flash(t('added_to_cart'), 'success')
        destination = {'cart': url_for('cart'), 'checkout': url_for('checkout'), 'product': url_for('product_detail', product_id=product['id'])}
        return redirect(destination.get(request.form.get('next'), url_for('shop')), code=303)

    @app.get('/cart')
    def cart():
        items, subtotal = load_cart()
        return render_template('cart.html', page='cart', items=items, subtotal=subtotal, delivery=app.config['DELIVERY_FEE_CENTS'] if items else 0)

    @app.post('/cart/update')
    def cart_update():
        cart = session.get('cart', {})
        key = str(request.form.get('product_id', type=int))
        product = db().execute('SELECT stock FROM products WHERE id=? AND active=1', (key,)).fetchone()
        quantity = request.form.get('quantity', 0, type=int) or 0
        if not product or quantity <= 0 or request.form.get('remove'):
            cart.pop(key, None)
        else:
            cart[key] = min(quantity, product['stock'], MAX_QUANTITY)
            if cart[key] < quantity:
                flash(t('stock_limited'), 'error')
            if not cart[key]:
                cart.pop(key)
        session['cart'] = cart
        return redirect(url_for('cart'), code=303)

    ADDRESS_FIELDS = ('first_name', 'last_name', 'phone', 'province', 'district', 'commune', 'street')

    def local_phone(phone):
        # Shown after the +855 prefix in the form: +85512345678 becomes 12 345 678.
        if not phone.startswith('+855'):
            return phone
        digits = phone[4:]
        return f'{digits[:2]} {digits[2:5]} {digits[5:]}'.strip()

    def render_checkout(values, errors, status=200):
        items, subtotal = load_cart()
        delivery = app.config['DELIVERY_FEE_CENTS']
        lang = session.get('language', 'en')
        # Options for the chosen province and district are rendered here too, so a re-shown form keeps its choices.
        places = {'provinces': locations.provinces(lang), 'districts': locations.children('districts', values.get('province'), lang),
                  'communes': locations.children('communes', values.get('district'), lang)}
        return render_template('checkout.html', page='checkout', items=items, subtotal=subtotal, delivery=delivery,
                               values=values, errors=errors, methods=payment_methods(), places=places,
                               place_name=lambda row: locations.name(row, lang)), status

    @app.get('/checkout')
    def checkout():
        if not session.get('cart'):
            return redirect(url_for('cart'))
        # Signing in is optional: it only pre-fills and saves the delivery address.
        customer = current_customer()
        saved = db().execute('SELECT * FROM customer_addresses WHERE customer_id=?', (customer['id'],)).fetchone() if customer else None
        values = dict(saved) if saved else {'phone': customer['phone'], 'save_address': '1'} if customer else {'phone': ''}
        values['phone'] = local_phone(values['phone']) if values['phone'] else ''
        values['payment_method'] = next(iter(payment_methods()), '')
        return render_checkout(values, {})

    @app.post('/checkout')
    @limiter.limit('10 per minute;60 per hour')
    def place_order():
        values = {key: request.form.get(key, '').strip() for key in (*ADDRESS_FIELDS, 'note', 'payment_method', 'save_address')}
        items, subtotal = load_cart()
        if not items:
            return redirect(url_for('cart'), code=303)
        errors = {}
        for key, minimum, maximum in [('first_name', 1, 60), ('last_name', 1, 60), ('street', 2, 200)]:
            if not minimum <= len(values[key]) <= maximum:
                errors[key] = t('error_' + key)
        # The form shows +855 in front, so a number typed without the leading 0 is still Cambodian.
        typed = values['phone']
        phone = normalize_phone(typed if typed.startswith(('0', '+', '855')) else '0' + typed)
        if not phone:
            errors['phone'] = t('error_delivery_phone')
        lang = session.get('language', 'en')
        place = locations.find(values['province'], values['district'], values['commune'])
        if not place:
            # Point at the first level that is missing or does not belong to the one above it.
            district_codes = [row[0] for row in locations.children('districts', values['province'], lang)]
            key = 'province' if not district_codes else 'district' if values['district'] not in district_codes else 'commune'
            errors[key] = t('error_' + key)
        if len(values['note']) > 500:
            errors['note'] = t('error_note')
        if values['payment_method'] not in payment_methods():
            errors['payment_method'] = t('error_payment_method')
        if errors:
            return render_checkout(values, errors, 422)
        name = f"{values['first_name']} {values['last_name']}"
        address, city = locations.describe(place, values['street'], lang)
        delivery = app.config['DELIVERY_FEE_CENTS']
        token = secrets.token_urlsafe(16)
        customer = current_customer()
        connection = db()
        try:
            connection.execute('BEGIN IMMEDIATE')
            for item in items:
                # Decrement stock only when enough remains, so concurrent orders cannot oversell.
                if not connection.execute('UPDATE products SET stock=stock-? WHERE id=? AND active=1 AND stock>=?', (item['quantity'], item['product']['id'], item['quantity'])).rowcount:
                    connection.rollback()
                    return render_checkout(values, {'form': t('stock_changed')}, 409)
            order_id = connection.execute(
                'INSERT INTO orders(token,customer_id,name,phone,email,address,city,note,payment_method,subtotal_cents,delivery_cents,total_cents,language) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (token, customer['id'] if customer else None, name, phone, '', address, city, values['note'], values['payment_method'],
                 subtotal, delivery, subtotal + delivery, lang)).lastrowid
            connection.executemany('INSERT INTO order_items(order_id,product_id,name,unit_cents,quantity) VALUES(?,?,?,?,?)',
                                   [(order_id, item['product']['id'], item['product']['name'], item['product']['price_cents'], item['quantity']) for item in items])
            if customer:
                connection.execute("UPDATE customers SET name=? WHERE id=? AND name=''", (name, customer['id']))
            if customer and values['save_address']:
                saved = (customer['id'], values['first_name'], values['last_name'], phone, values['province'], values['district'], values['commune'], values['street'])
                connection.execute('INSERT INTO customer_addresses(customer_id,first_name,last_name,phone,province,district,commune,street) VALUES(?,?,?,?,?,?,?,?) '
                                   'ON CONFLICT(customer_id) DO UPDATE SET first_name=excluded.first_name,last_name=excluded.last_name,phone=excluded.phone,'
                                   'province=excluded.province,district=excluded.district,commune=excluded.commune,street=excluded.street', saved)
            connection.commit()
        except database.ERRORS:
            connection.rollback()
            app.logger.exception('Order persistence failed')
            return render_checkout(values, {'form': t('error_save')}, 503)
        session.pop('cart', None)
        if values['payment_method'] == 'payway':
            return redirect(url_for('order_pay', token=token), code=303)
        flash(t('order_placed'), 'success')
        return redirect(url_for('order', token=token), code=303)

    def code_hash(phone, code):
        return hash_code(app.config['SECRET_KEY'], phone, code)

    def render_login(step, errors=None, status=200, phone_input=''):
        telegram_link, code_sent = None, True
        if step == 'code' and app.config['TELEGRAM_BOT_TOKEN']:
            latest = db().execute('SELECT start_token,code_hash FROM login_codes WHERE phone=? ORDER BY id DESC LIMIT 1', (session.get('login_phone'),)).fetchone()
            if latest:
                telegram_link = f"https://t.me/{app.config['TELEGRAM_BOT_USERNAME']}?start={latest['start_token']}"
                code_sent = bool(latest['code_hash'])
        return render_template('account_login.html', page='account_login', step=step, errors=errors or {}, phone_input=phone_input,
                               login_phone=session.get('login_phone', ''), next=safe_target(request.values.get('next'), ''),
                               telegram_link=telegram_link, code_sent=code_sent), status

    @app.get('/account/login')
    def account_login():
        if current_customer():
            return redirect(safe_target(request.args.get('next'), url_for('account')))
        return render_login('phone')

    @app.post('/account/login')
    # A loose abuse guard only; the real per-number and per-address limits below count codes actually sent.
    @limiter.limit('30 per minute;200 per hour')
    def send_login_code():
        phone_input = request.form.get('phone', '').strip()[:40]
        phone = normalize_phone(phone_input)
        if not phone:
            return render_login('phone', {'phone': t('error_phone_login')}, 422, phone_input)
        now = int(time.time())
        recent = db().execute('SELECT count(*), max(created_at) FROM login_codes WHERE phone=? AND created_at>?', (phone, now - 3600)).fetchone()
        # Per-number limits protect customers from code spam and the shop from Telegram charges.
        if recent[0] >= 5 or (recent[1] and now - recent[1] < 60):
            return render_login('phone', {'phone': t('error_code_wait')}, 429, phone_input)
        address = get_remote_address()
        per_address = db().execute('SELECT count(*) FROM login_codes WHERE ip=? AND created_at>?', (address, now - 3600)).fetchone()[0]
        last_minute = db().execute('SELECT count(*) FROM login_codes WHERE ip=? AND created_at>?', (address, now - 60)).fetchone()[0]
        if per_address >= 20 or last_minute >= 5:
            return render_login('phone', {'phone': t('error_429')}, 429, phone_input)
        if app.config['TELEGRAM_BOT_TOKEN']:
            try:
                telegram_bot.bot_username(app)
            except telegram_bot.TelegramError as error:
                app.logger.error('Telegram bot is not reachable: %s', error)
                return render_login('phone', {'phone': t('error_telegram')}, 502, phone_input)
            # The bot sends the code once the customer opens it and confirms this number.
            login_id = db().execute('INSERT INTO login_codes(phone,code_hash,ip,start_token,created_at,expires_at) VALUES(?,?,?,?,?,?)',
                                    (phone, '', address, secrets.token_urlsafe(16), now, now + LINK_TTL)).lastrowid
            db().commit()
            chat = db().execute('SELECT chat_id FROM telegram_chats WHERE phone=?', (phone,)).fetchone()
            if chat:
                try:
                    telegram_bot.send_code(app, db(), login_id, chat['chat_id'])
                except telegram_bot.TelegramError as error:
                    # For example the customer blocked the bot; they can reopen it from the link instead.
                    app.logger.warning('Could not send a code to a known Telegram chat: %s', error)
        else:
            code = new_code()
            if not send_telegram_code(phone, code):
                return render_login('phone', {'phone': t('error_telegram')}, 502, phone_input)
            db().execute('INSERT INTO login_codes(phone,code_hash,ip,created_at,expires_at) VALUES(?,?,?,?,?)', (phone, code_hash(phone, code), address, now, now + CODE_TTL))
            db().commit()
            if app.config['TELEGRAM_DEV_MODE'] and not app.config['TELEGRAM_GATEWAY_TOKEN']:
                flash(f"{t('dev_code_notice')} {code}", 'success')
        session['login_phone'] = phone
        return redirect(url_for('verify_login_code', next=safe_target(request.form.get('next'), '') or None), code=303)

    @app.route('/account/verify', methods=['GET', 'POST'])
    @limiter.limit('10 per minute;40 per hour', methods=['POST'])
    def verify_login_code():
        phone = session.get('login_phone')
        if not phone:
            return redirect(url_for('account_login'))
        if request.method == 'GET':
            return render_login('code')
        latest = db().execute('SELECT * FROM login_codes WHERE phone=? ORDER BY id DESC LIMIT 1', (phone,)).fetchone()
        if not latest or latest['expires_at'] < time.time():
            return render_login('code', {'code': t('error_code_expired')}, 422)
        if not latest['code_hash']:
            return render_login('code', {'code': t('error_code_not_sent')}, 422)
        if latest['attempts'] >= CODE_MAX_ATTEMPTS:
            return render_login('code', {'code': t('error_code_attempts')}, 429)
        entered = re.sub(r'\D', '', request.form.get('code', ''))[:8]
        if not hmac.compare_digest(latest['code_hash'], code_hash(phone, entered)):
            db().execute('UPDATE login_codes SET attempts=attempts+1 WHERE id=?', (latest['id'],))
            db().commit()
            return render_login('code', {'code': t('error_code')}, 422)
        db().execute('DELETE FROM login_codes WHERE phone=?', (phone,))
        db().execute('INSERT INTO customers(phone) VALUES(?) ON CONFLICT(phone) DO NOTHING', (phone,))
        customer_id = db().execute('SELECT id FROM customers WHERE phone=?', (phone,)).fetchone()['id']
        db().commit()
        kept = {key: session[key] for key in ('cart', 'language', 'admin_id') if key in session}
        session.clear()
        session.update(kept, customer_id=customer_id)
        flash(t('logged_in'), 'success')
        return redirect(safe_target(request.args.get('next'), url_for('account')), code=303)

    @app.get('/account')
    @customer_required
    def account():
        orders = db().execute('SELECT * FROM orders WHERE customer_id=? ORDER BY id DESC LIMIT 100', (current_customer()['id'],)).fetchall()
        return render_template('account.html', page='account', orders=orders)

    @app.post('/account/logout')
    def account_logout():
        session.pop('customer_id', None)
        session.pop('login_phone', None)
        return redirect(url_for('index'), code=303)

    def find_order(token):
        found = db().execute('SELECT * FROM orders WHERE token=?', (token,)).fetchone()
        if not found:
            abort(404)
        return found

    @app.get('/orders/<token>')
    def order(token):
        found = find_order(token)
        if found['payment_method'] == 'payway' and found['payment_status'] == 'unpaid':
            found = reconcile_payway(found)
        items = db().execute('SELECT * FROM order_items WHERE order_id=? ORDER BY id', (found['id'],)).fetchall()
        return render_template('order.html', page='order', order=found, items=items, errors={})

    def reconcile_payway(found):
        """Ask PayWay about this order's recent attempts and mark the order paid once one is approved."""
        attempts = db().execute("SELECT * FROM payway_transactions WHERE order_id=? AND status='pending' AND created_at>? ORDER BY created_at DESC LIMIT 3",
                                (found['id'], int(time.time()) - 7 * 86400)).fetchall()
        for attempt in attempts:
            try:
                result = payway.check_transaction(app.config, attempt['tran_id'])
            except payway.PayWayError as error:
                app.logger.warning('PayWay check failed for %s: %s', attempt['tran_id'], error)
                break
            payment_status = (result.get('data') or {}).get('payment_status')
            if payway.is_approved(result, attempt['amount_cents']) and attempt['amount_cents'] == found['total_cents']:
                apv = str(result['data'].get('apv', ''))[:20]
                db().execute("UPDATE payway_transactions SET status='approved', apv=? WHERE tran_id=?", (apv, attempt['tran_id']))
                db().execute("UPDATE orders SET payment_status='paid', payment_reference=? WHERE id=? AND payment_status='unpaid'",
                             (f"ABA PayWay {attempt['tran_id']} / APV {apv}", found['id']))
                db().commit()
                return find_order(found['token'])
            if payment_status in ('DECLINED', 'CANCELLED'):
                db().execute('UPDATE payway_transactions SET status=? WHERE tran_id=?', (payment_status.lower(), attempt['tran_id']))
                db().commit()
        return found

    @app.get('/orders/<token>/pay')
    @limiter.limit('10 per minute;30 per hour')
    def order_pay(token):
        """Send the customer to the ABA PayWay checkout with a freshly signed request."""
        found = find_order(token)
        if not payway.enabled(app.config) or found['payment_method'] != 'payway' or found['payment_status'] != 'unpaid' or found['status'] == 'cancelled':
            return redirect(url_for('order', token=token))
        items = db().execute('SELECT * FROM order_items WHERE order_id=? ORDER BY id', (found['id'],)).fetchall()
        tran_id = payway.new_tran_id(found['id'])
        db().execute('INSERT INTO payway_transactions(tran_id,order_id,amount_cents,created_at) VALUES(?,?,?,?)',
                     (tran_id, found['id'], found['total_cents'], int(time.time())))
        db().commit()
        order_url = url_for('order', token=token, _external=True)
        fields = payway.purchase_form(app.config, tran_id, found, items, return_url=url_for('payway_callback', _external=True),
                                      cancel_url=order_url, continue_url=order_url)
        return render_template('payway_redirect.html', page='order', order=found,
                               action=app.config['PAYWAY_BASE_URL'].rstrip('/') + payway.PURCHASE_PATH, fields=fields)

    @app.post('/telegram/webhook')
    @csrf.exempt
    def telegram_webhook():
        """Telegram bot messages in webhook mode (used on Vercel, where nothing can poll in the background)."""
        token = app.config['TELEGRAM_BOT_TOKEN']
        if not token or not hmac.compare_digest(request.headers.get('X-Telegram-Bot-Api-Secret-Token', ''), telegram_bot.webhook_secret(token)):
            abort(403)
        try:
            telegram_bot.handle_update(app, request.get_json(silent=True) or {})
        except Exception:
            # Always answer 200 so Telegram does not keep retrying one bad message.
            app.logger.exception('Could not handle Telegram webhook update')
        return jsonify(ok=True)

    @app.post('/payway/callback')
    @csrf.exempt
    @limiter.limit('120 per minute')
    def payway_callback():
        """PayWay's payment notice. Only a hint: the status is always confirmed with PayWay before an order is marked paid."""
        data = request.get_json(silent=True) or request.form
        tran_id = str(data.get('tran_id', ''))[:20]
        attempt = db().execute('SELECT order_id FROM payway_transactions WHERE tran_id=?', (tran_id,)).fetchone()
        if attempt:
            found = db().execute('SELECT * FROM orders WHERE id=?', (attempt['order_id'],)).fetchone()
            if found['payment_status'] == 'unpaid':
                reconcile_payway(found)
        return jsonify(ok=True)

    @app.post('/orders/<token>/payment')
    @limiter.limit('10 per minute;30 per hour')
    def order_payment(token):
        found = find_order(token)
        if found['payment_method'] != 'bank' or found['payment_status'] not in ('unpaid', 'submitted') or found['status'] == 'cancelled':
            abort(400)
        reference = request.form.get('reference', '').strip()
        if not 3 <= len(reference) <= 100:
            items = db().execute('SELECT * FROM order_items WHERE order_id=? ORDER BY id', (found['id'],)).fetchall()
            return render_template('order.html', page='order', order=found, items=items, errors={'reference': t('error_reference')}), 422
        db().execute("UPDATE orders SET payment_reference=?, payment_status='submitted' WHERE id=?", (reference, found['id']))
        db().commit()
        flash(t('payment_submitted'), 'success')
        return redirect(url_for('order', token=token), code=303)

    @app.get('/set-language/<language>')
    def set_language(language):
        if language not in translations:
            abort(404)
        session['language'] = language
        session.permanent = True
        response = redirect(safe_target(request.args.get('next', '/')))
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

    def admin_counts():
        """Numbers shown on the admin tabs: what needs attention now."""
        one = lambda sql, *args: db().execute(sql, args).fetchone()[0]
        return {'orders': one("SELECT count(*) FROM orders WHERE status='pending'"),
                'payments': one("SELECT count(*) FROM orders WHERE payment_status='submitted' AND status!='cancelled'"),
                'messages': one("SELECT count(*) FROM messages WHERE status='new'"),
                'low_stock': one('SELECT count(*) FROM products WHERE active=1 AND stock<=?', LOW_STOCK)}

    def items_by_order(orders):
        grouped = {}
        if orders:
            ids = [order['id'] for order in orders]
            for item in db().execute(f"SELECT * FROM order_items WHERE order_id IN ({','.join('?' * len(ids))}) ORDER BY id", ids):
                grouped.setdefault(item['order_id'], []).append(item)
        return grouped

    @app.get('/admin', defaults={'view': 'overview'})
    @app.get('/admin/<any(orders, products, messages, retailers):view>')
    @admin_required
    def admin(view):
        data = dict(view=view, counts=admin_counts(), order_statuses=ORDER_STATUSES, payment_statuses=PAYMENT_STATUSES, low_stock=LOW_STOCK)
        if view == 'overview':
            data['revenue'] = db().execute("SELECT coalesce(sum(total_cents),0) FROM orders WHERE payment_status='paid' AND status!='cancelled'").fetchone()[0]
            data['orders'] = db().execute("SELECT * FROM orders WHERE status IN ('pending','confirmed','shipped') OR payment_status='submitted' ORDER BY id DESC LIMIT 5").fetchall()
            data['messages'] = db().execute("SELECT * FROM messages WHERE status='new' ORDER BY id DESC LIMIT 5").fetchall()
            data['low_products'] = db().execute('SELECT * FROM products WHERE active=1 AND stock<=? ORDER BY stock, id', (LOW_STOCK,)).fetchall()
        elif view == 'orders':
            status = request.args.get('status', '')
            if status not in ('', 'payment', *ORDER_STATUSES):
                abort(400)
            if status == 'payment':
                where, args = "payment_status='submitted' AND status!='cancelled'", ()
            else:
                where, args = "(?='' OR status=?)", (status, status)
            data['status'] = status
            data['orders'] = db().execute(f'SELECT * FROM orders WHERE {where} ORDER BY id DESC LIMIT 200', args).fetchall()
            data['order_items'] = items_by_order(data['orders'])
        elif view == 'products':
            data['products'] = db().execute('SELECT * FROM products ORDER BY active DESC, id').fetchall()
            data['product_images'] = product_images
            data['photo_limit_mb'] = MAX_PHOTO_BYTES // (1024 * 1024)
            data['photo_size'] = PHOTO_SIZE
        elif view == 'messages':
            status = request.args.get('status', '')
            if status not in ('', 'new', 'read', 'archived'):
                abort(400)
            data['status'] = status
            data['messages'] = db().execute("SELECT * FROM messages WHERE (?='' OR status=?) ORDER BY id DESC LIMIT 200", (status, status)).fetchall()
            data['stats'] = dict(db().execute('SELECT status,count(*) FROM messages GROUP BY status').fetchall())
        else:
            data['stores'] = db().execute('SELECT * FROM retailers ORDER BY id DESC').fetchall()
        return render_template('admin.html', page='admin', **data)

    @app.post('/admin/orders/<int:order_id>')
    @admin_required
    def update_order(order_id):
        connection = db()
        connection.execute('BEGIN IMMEDIATE')
        current = connection.execute('SELECT status,payment_status,payment_method FROM orders WHERE id=?', (order_id,)).fetchone()
        if not current:
            connection.rollback()
            abort(404)
        action = request.form.get('action')
        if action:
            if action not in ORDER_ACTIONS:
                connection.rollback()
                abort(400)
            new_status, new_payment = ORDER_ACTIONS[action]
            status, payment_status = new_status or current['status'], new_payment or current['payment_status']
            # Completing a cash-on-delivery order means the cash was collected.
            if action == 'complete' and current['payment_method'] == 'cod' and payment_status == 'unpaid':
                payment_status = 'paid'
        else:
            status, payment_status = request.form.get('status'), request.form.get('payment_status')
        if status not in ORDER_STATUSES or payment_status not in PAYMENT_STATUSES:
            connection.rollback()
            abort(400)
        # Return items to stock when an order is cancelled, and take them again if it is reopened.
        if (current['status'] == 'cancelled') != (status == 'cancelled'):
            sign = 1 if status == 'cancelled' else -1
            connection.execute('UPDATE products SET stock=(CASE WHEN stock+?*(SELECT coalesce(sum(quantity),0) FROM order_items WHERE order_id=? AND product_id=products.id) < 0 THEN 0 ELSE stock+?*(SELECT coalesce(sum(quantity),0) FROM order_items WHERE order_id=? AND product_id=products.id) END) WHERE id IN (SELECT product_id FROM order_items WHERE order_id=?)', (sign, order_id, sign, order_id, order_id))
        connection.execute('UPDATE orders SET status=?, payment_status=? WHERE id=?', (status, payment_status, order_id))
        connection.commit()
        flash(t('order_updated').replace('{id}', str(order_id)), 'success')
        return redirect(safe_target(request.form.get('back'), url_for('admin', view='orders')))

    @app.post('/admin/products')
    @admin_required
    def save_product():
        fields = {key: request.form.get(key, '').strip() for key in ('name', 'name_km', 'description', 'description_km', 'image')}
        price = parse_money(request.form.get('price', ''))
        stock = request.form.get('stock', type=int)
        product_id = request.form.get('id', type=int)
        if request.form.get('id') and product_id is None:
            abort(400)
        current = db().execute('SELECT image FROM products WHERE id=?', (product_id,)).fetchone() if product_id else None
        # Besides the bundled pictures, a product may keep the photo it already has.
        allowed_images = set(product_images) | ({current['image']} if current else set())
        if not 2 <= len(fields['name']) <= 120 or len(fields['name_km']) > 120 or len(fields['description']) > 500 or len(fields['description_km']) > 500 \
                or fields['image'] not in allowed_images or price is None or stock is None or not 0 <= stock <= 100000:
            flash(t('error_product'), 'error')
            return redirect(url_for('admin', view='products'))
        upload = request.files.get('photo')
        if upload and upload.filename:
            photo = webp_photo(upload)
            if photo is None:
                flash(t('error_photo'), 'error')
                return redirect(url_for('admin', view='products'))
            photo_id = db().execute('INSERT INTO product_photos(data,created_at) VALUES(?,?)', (photo, int(time.time()))).lastrowid
            fields['image'] = f'{PHOTO_PREFIX}{photo_id}.webp'
        values = (*fields.values(), price, stock, 1 if request.form.get('active') else 0)
        if product_id:
            if not db().execute('UPDATE products SET name=?,name_km=?,description=?,description_km=?,image=?,price_cents=?,stock=?,active=? WHERE id=?', (*values, product_id)).rowcount:
                abort(404)
        else:
            db().execute('INSERT INTO products(name,name_km,description,description_km,image,price_cents,stock,active) VALUES(?,?,?,?,?,?,?,?)', values)
        # Drop uploaded photos that no product uses any more (for example after a picture was replaced).
        used = {row[0] for row in db().execute('SELECT image FROM products').fetchall()}
        for (photo_id,) in db().execute('SELECT id FROM product_photos').fetchall():
            if f'{PHOTO_PREFIX}{photo_id}.webp' not in used:
                db().execute('DELETE FROM product_photos WHERE id=?', (photo_id,))
        db().commit()
        flash(t('saved'), 'success')
        return redirect(url_for('admin', view='products'))

    @app.post('/admin/messages/<int:message_id>/status')
    @admin_required
    def message_status(message_id):
        status = request.form.get('status')
        if status not in ('new', 'read', 'archived'):
            abort(400)
        if not db().execute('UPDATE messages SET status=? WHERE id=?', (status, message_id)).rowcount:
            abort(404)
        db().commit()
        return redirect(safe_target(request.form.get('back'), url_for('admin', view='messages')))

    @app.post('/admin/retailers')
    @admin_required
    def save_retailer():
        fields = {key: request.form.get(key, '').strip() for key in ('name', 'country', 'city', 'address', 'phone', 'email')}
        retailer_id = request.form.get('id', type=int)
        if request.form.get('id') and retailer_id is None:
            abort(400)
        if any(not fields[key] or len(fields[key]) > 200 for key in ('name', 'country', 'city', 'address')) or len(fields['email']) > 254 or (fields['email'] and not re.fullmatch(EMAIL_RE, fields['email'])) or (fields['phone'] and not re.fullmatch(PHONE_RE, fields['phone'])):
            flash(t('error_retailer'), 'error')
        else:
            if retailer_id:
                if not db().execute('UPDATE retailers SET name=?,country=?,city=?,address=?,phone=?,email=?,is_demo=0 WHERE id=?', (*fields.values(), retailer_id)).rowcount:
                    abort(404)
            else:
                db().execute('INSERT INTO retailers(name,country,city,address,phone,email) VALUES(?,?,?,?,?,?)', tuple(fields.values()))
            db().commit()
            flash(t('saved'), 'success')
        return redirect(url_for('admin', view='retailers'))

    @app.post('/admin/retailers/<int:retailer_id>/delete')
    @admin_required
    def delete_retailer(retailer_id):
        db().execute('DELETE FROM retailers WHERE id=?', (retailer_id,))
        db().commit()
        return redirect(url_for('admin', view='retailers'))

    @app.template_filter('money')
    def money(cents):
        return f"{app.config['CURRENCY_SYMBOL']}{cents / 100:,.2f}"

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
            # Keep people on the sign-in form, with an explanation, when a sign-in rate limit is hit.
            if code == 429 and request.endpoint == 'send_login_code':
                return render_login('phone', {'phone': t('error_429')}, 429, request.form.get('phone', '')[:40])
            if code == 429 and request.endpoint == 'verify_login_code':
                return render_login('code', {'code': t('error_429')}, 429)
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


@app.cli.command('telegram-bot')
def telegram_bot_command():
    """Run only the Telegram sign-in bot, for servers that start the website with waitress."""
    if not app.config['TELEGRAM_BOT_TOKEN'] or not telegram_bot.start_polling(app):
        raise click.ClickException('Set a valid TELEGRAM_BOT_TOKEN in .env first.')
    click.echo(f"Bot @{app.config['TELEGRAM_BOT_USERNAME']} is running. Press Ctrl+C to stop.")
    while True:
        time.sleep(3600)


@app.cli.command('telegram-webhook')
@click.argument('site_url', required=False)
@click.option('--delete', is_flag=True, help='Remove the webhook so the bot can poll from this computer again.')
def telegram_webhook_command(site_url, delete):
    """Connect the bot to a public site, e.g. https://empresscambodia.vercel.app (or --delete to undo)."""
    if not app.config['TELEGRAM_BOT_TOKEN']:
        raise click.ClickException('Set TELEGRAM_BOT_TOKEN in .env first.')
    if delete:
        telegram_bot.api(app.config['TELEGRAM_BOT_TOKEN'], 'deleteWebhook')
        click.echo('Webhook removed; the bot can poll from this computer again.')
        return
    if not site_url or not site_url.startswith('https://'):
        raise click.ClickException('Give the public https:// address of the site.')
    telegram_bot.set_webhook(app, site_url)
    click.echo(f'Bot @{telegram_bot.bot_username(app)} now sends messages to {site_url.rstrip("/")}/telegram/webhook')


if __name__ == '__main__':
    if app.config['TELEGRAM_BOT_TOKEN']:
        telegram_bot.start_polling(app)
    app.run(host='127.0.0.1', port=5050, debug=False)
