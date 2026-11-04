import io
import re

import pytest

import app as app_module
from test_app import app, client, connect_db, login, token  # noqa: F401  (pytest fixtures)


@pytest.fixture(autouse=True)
def telegram_codes(monkeypatch):
    """Capture login codes instead of calling the Telegram Gateway."""
    sent = []
    monkeypatch.setattr(app_module, 'send_telegram_code', lambda phone, code: sent.append((phone, code)) or True)
    return sent


def sign_in(client, codes, phone='012 345 678'):
    client.post('/account/login', data={'csrf_token': token(client, '/account/login'), 'phone': phone})
    return client.post('/account/verify', data={'csrf_token': token(client, '/account/verify'), 'code': codes[-1][1]})


def add_to_cart(client, product_id=1, quantity=2):
    return client.post('/cart/add', data={'csrf_token': token(client, '/shop'), 'product_id': product_id, 'quantity': quantity})


def order_form(client, **changes):
    data = dict(csrf_token=token(client, '/checkout'), first_name='Sok', last_name='Dara', phone='012 345 678', province='12', district='1201',
                commune='120101', street='House 12, Street 51', note='', payment_method='bank', save_address='1')
    data.update(changes)
    return data


def query(app, sql, *args):
    with connect_db(app) as connection:
        return connection.execute(sql, args).fetchall()


def test_shop_cart_and_checkout(client, app, telegram_codes):
    assert client.get('/checkout').location == '/cart'
    shop = client.get('/shop').text
    assert '$18.00' in shop and 'Add to cart' in shop
    assert add_to_cart(client).status_code == 303
    assert add_to_cart(client, product_id=999).status_code == 404
    cart = client.get('/cart').text
    assert '$36.00' in cart and '$37.50' in cart
    assert 'class="cart-count" aria-hidden="true">2<' in cart
    sign_in(client, telegram_codes)
    assert 'Cash on delivery' not in client.get('/checkout').text
    assert client.post('/checkout', data=order_form(client, payment_method='cod')).status_code == 422
    response = client.post('/checkout', data=order_form(client))
    assert response.status_code == 303
    page = client.get(response.location).text
    assert 'Bank transfer' in page and '$37.50' in page and 'Sok Dara' in page
    assert query(app, 'SELECT total_cents,payment_method,status,payment_status,phone,customer_id FROM orders') == [(3750, 'bank', 'pending', 'unpaid', '+85512345678', 1)]
    assert query(app, 'SELECT name,unit_cents,quantity FROM order_items') == [('The Daily Glow', 1800, 2)]
    assert query(app, 'SELECT address,city FROM orders') == [('House 12, Street 51, Tonle Basak, Chamkar Mon', 'Phnom Penh')]
    assert query(app, 'SELECT stock FROM products WHERE id=1') == [(23,)]
    assert 'Your cart is empty' in client.get('/cart').text
    assert client.get('/orders/not-a-real-token').status_code == 404


def test_cart_update_remove_and_stock_limits(client, app, telegram_codes):
    sign_in(client, telegram_codes)
    add_to_cart(client, quantity=50)
    with client.session_transaction() as session:
        assert session['cart'] == {'1': 20}
    client.post('/cart/update', data={'csrf_token': token(client, '/cart'), 'product_id': 1, 'quantity': 3})
    with client.session_transaction() as session:
        assert session['cart'] == {'1': 3}
    client.post('/cart/update', data={'csrf_token': token(client, '/cart'), 'product_id': 1, 'quantity': 3, 'remove': '1'})
    with client.session_transaction() as session:
        assert session['cart'] == {}
    add_to_cart(client, quantity=2)
    # Stock drops after the item is in the cart: checkout must refuse rather than oversell.
    with connect_db(app) as connection:
        connection.execute('UPDATE products SET stock=1 WHERE id=1')
    response = client.post('/checkout', data=order_form(client))
    assert response.status_code == 409 and 'no longer have enough stock' in response.text
    assert query(app, 'SELECT count(*) FROM orders') == [(0,)]
    assert query(app, 'SELECT stock FROM products WHERE id=1') == [(1,)]



def test_guest_checkout_without_account(client, app):
    add_to_cart(client)
    page = client.get('/checkout')
    assert page.status_code == 200 and 'name="save_address"' not in page.text and 'Sign in to use your saved address' in page.text
    response = client.post('/checkout', data=order_form(client))
    assert response.status_code == 303 and response.location.startswith('/orders/')
    assert client.get(response.location).status_code == 200
    assert query(app, 'SELECT customer_id,name FROM orders') == [(None, 'Sok Dara')]
    assert query(app, 'SELECT count(*) FROM customers') == [(0,)]
    assert query(app, 'SELECT count(*) FROM customer_addresses') == [(0,)]


def test_checkout_validation(client, app, telegram_codes):
    sign_in(client, telegram_codes)
    add_to_cart(client)
    response = client.post('/checkout', data=order_form(client, first_name='Sok', last_name='', phone='abc', street='x', payment_method='crypto'))
    assert response.status_code == 422
    for message in ['last name', 'valid phone number', 'house number and street', 'payment method']:
        assert message in response.text
    # The chosen district and commune lists are rendered again with the choice kept.
    assert 'value="Sok"' in response.text and '<option value="120101" selected>Tonle Basak</option>' in response.text
    # A commune that is not in the chosen district is refused, pointing at the commune list.
    response = client.post('/checkout', data=order_form(client, commune='010201'))
    assert response.status_code == 422 and 'choose a commune' in response.text
    assert client.post('/checkout', data=order_form(client, district='0102')).status_code == 422
    assert client.post('/checkout', data=order_form(client, province='99')).status_code == 422
    assert query(app, 'SELECT count(*) FROM orders') == [(0,)]
    app.config['PAYMENT_ACCOUNT_NUMBER'] = ''
    assert 'Bank transfer' not in client.get('/checkout').text
    assert client.post('/checkout', data=order_form(client, payment_method='bank')).status_code == 422


def test_bank_transfer_and_admin_order_management(client, app, telegram_codes):
    sign_in(client, telegram_codes)
    add_to_cart(client, product_id=2, quantity=3)
    location = client.post('/checkout', data=order_form(client, payment_method='bank')).location
    page = client.get(location).text
    assert '000 111 222' in page and 'Test Bank' in page and 'EMP-1' in page and '$30.00' in page
    order_token = location.rsplit('/', 1)[1]
    payment_token = re.search(r'name="csrf_token" value="([^"]+)"', page)[1]
    assert client.post(f'/orders/{order_token}/payment', data={'csrf_token': payment_token, 'reference': 'x'}).status_code == 422
    assert client.post(f'/orders/{order_token}/payment', data={'csrf_token': payment_token, 'reference': 'ABA-778899'}).status_code == 303
    assert query(app, 'SELECT payment_status,payment_reference FROM orders') == [('submitted', 'ABA-778899')]
    assert query(app, 'SELECT stock FROM products WHERE id=2') == [(22,)]
    # Customers cannot change order status themselves.
    assert client.post('/admin/orders/1', data={'csrf_token': payment_token, 'status': 'confirmed', 'payment_status': 'paid'}).status_code == 302
    assert query(app, 'SELECT status FROM orders') == [('pending',)]
    login(client)
    admin = client.get('/admin').text
    assert 'ABA-778899' in admin and 'Sok Dara' in admin
    admin_token = token(client, '/admin')
    assert client.post('/admin/orders/1', data={'csrf_token': admin_token, 'status': 'confirmed', 'payment_status': 'paid'}).status_code == 302
    assert query(app, 'SELECT status,payment_status FROM orders') == [('confirmed', 'paid')]
    client.post('/admin/orders/1', data={'csrf_token': admin_token, 'status': 'cancelled', 'payment_status': 'refunded'})
    assert query(app, 'SELECT stock FROM products WHERE id=2') == [(25,)]
    client.post('/admin/orders/1', data={'csrf_token': admin_token, 'status': 'cancelled', 'payment_status': 'refunded'})
    assert query(app, 'SELECT stock FROM products WHERE id=2') == [(25,)]
    assert client.post('/admin/orders/1', data={'csrf_token': admin_token, 'status': 'lost', 'payment_status': 'paid'}).status_code == 400
    assert client.post('/admin/orders/99', data={'csrf_token': admin_token, 'status': 'pending', 'payment_status': 'paid'}).status_code == 404
    assert client.post(f'/orders/{order_token}/payment', data={'csrf_token': admin_token, 'reference': 'ABA-1'}).status_code == 400


def test_admin_product_management(client, app):
    product = dict(name='Rice Bran Soap', name_km='សាប៊ូ', description='Gentle bar.', description_km='', price='4.50', stock='10', image='botanical.webp', active='1')
    assert client.post('/admin/products', data={**product, 'csrf_token': token(client, '/shop')}).status_code == 302
    assert query(app, 'SELECT count(*) FROM products') == [(3,)]
    login(client)
    admin_token = token(client, '/admin')
    assert client.post('/admin/products', data={**product, 'csrf_token': admin_token}).status_code == 302
    shop = client.get('/shop').text
    assert 'Rice Bran Soap' in shop and '$4.50' in shop
    client.get('/set-language/km?next=/')
    assert 'សាប៊ូ' in client.get('/shop').text
    for bad in [{'price': '-1'}, {'price': '1.234'}, {'price': 'abc'}, {'stock': '-2'}, {'image': '../app.py'}, {'name': ''}]:
        client.post('/admin/products', data={**product, **bad, 'csrf_token': admin_token})
    assert query(app, 'SELECT count(*) FROM products') == [(4,)]
    product_id = query(app, 'SELECT id FROM products WHERE name=?', 'Rice Bran Soap')[0][0]
    hidden = {**product, 'id': str(product_id), 'price': '5', 'csrf_token': admin_token}
    del hidden['active']
    assert client.post('/admin/products', data=hidden).status_code == 302
    assert query(app, 'SELECT price_cents,active FROM products WHERE id=?', product_id) == [(500, 0)]
    assert 'Rice Bran Soap' not in client.get('/shop').text
    assert client.post('/cart/add', data={'csrf_token': admin_token, 'product_id': product_id}).status_code == 404
    assert client.post('/admin/products', data={**hidden, 'id': 'abc'}).status_code == 400
    assert client.post('/admin/retailers', data={'csrf_token': admin_token, 'id': 'abc', 'name': 'x', 'country': 'x', 'city': 'x', 'address': 'x'}).status_code == 400



def picture(fmt='PNG', size=(2400, 1200)):
    from PIL import Image
    buffer = io.BytesIO()
    Image.new('RGB', size, (200, 120, 90)).save(buffer, fmt)
    buffer.seek(0)
    return buffer


def test_admin_uploads_product_photo(client, app):
    login(client)
    admin_token = token(client, '/admin')
    product_id = query(app, 'SELECT id FROM products ORDER BY id LIMIT 1')[0][0]
    form = dict(csrf_token=admin_token, id=str(product_id), name='Daily Glow', name_km='', description='', description_km='',
                price='18', stock='25', image='hero.webp', active='1')
    response = client.post('/admin/products', data={**form, 'photo': (picture(), 'pack.png')}, content_type='multipart/form-data')
    assert response.status_code == 302
    image = query(app, 'SELECT image FROM products WHERE id=?', product_id)[0][0]
    assert re.fullmatch(r'uploads/\d+\.webp', image)
    photo = client.get('/' + image)
    assert photo.status_code == 200 and photo.mimetype == 'image/webp' and 'immutable' in photo.headers['Cache-Control']
    assert 'Set-Cookie' not in app.test_client().get('/' + image).headers  # visitors' photo responses stay cacheable
    from PIL import Image
    assert max(Image.open(io.BytesIO(photo.data)).size) == app_module.PHOTO_SIZE
    assert '/' + image in client.get('/shop').text and '/' + image in client.get('/').text
    # Saving again without a new file keeps the uploaded photo.
    assert client.post('/admin/products', data={**form, 'image': image}, content_type='multipart/form-data').status_code == 302
    assert query(app, 'SELECT image FROM products WHERE id=?', product_id)[0][0] == image
    # A replacement photo removes the old one; files that are not pictures are refused.
    client.post('/admin/products', data={**form, 'image': image, 'photo': (picture('JPEG'), 'new.jpg')}, content_type='multipart/form-data')
    assert client.get('/' + image).status_code == 404
    assert query(app, 'SELECT count(*) FROM product_photos') == [(1,)]
    client.post('/admin/products', data={**form, 'photo': (io.BytesIO(b'not a picture'), 'x.png')}, content_type='multipart/form-data')
    assert query(app, 'SELECT count(*) FROM product_photos') == [(1,)]
    # Another product cannot borrow an uploaded photo through the image field.
    other = query(app, 'SELECT id FROM products ORDER BY id LIMIT 1 OFFSET 1')[0][0]
    current = query(app, 'SELECT image FROM products WHERE id=?', product_id)[0][0]
    client.post('/admin/products', data={**form, 'id': str(other), 'image': current}, content_type='multipart/form-data')
    assert query(app, 'SELECT image FROM products WHERE id=?', other)[0][0] != current


def test_default_address_and_khmer_address(client, app, telegram_codes):
    sign_in(client, telegram_codes)
    add_to_cart(client)
    page = client.get('/checkout').text
    # First checkout: phone comes from the account and saving the address is ticked.
    assert 'value="12 345 678"' in page and 'name="save_address" value="1" checked' in page
    assert 'name="district" required disabled' in page
    client.get('/set-language/km')
    # A number typed after the +855 prefix without its leading 0 is still accepted.
    assert client.post('/checkout', data=order_form(client, phone='15 663 024', province='01', district='0102', commune='010201')).status_code == 303
    assert query(app, 'SELECT phone,address,city FROM orders') == [('+85515663024', 'House 12, Street 51, ឃុំបន្ទាយនាង, ស្រុកមង្គលបូរី', 'បន្ទាយមានជ័យ')]
    assert query(app, 'SELECT first_name,phone,province,district,commune FROM customer_addresses') == [('Sok', '+85515663024', '01', '0102', '010201')]
    add_to_cart(client)
    page = client.get('/checkout').text
    assert 'value="15 663 024"' in page and '<option value="010201" selected>' in page
    # Leaving the box unticked keeps the saved address as it was.
    data = order_form(client, first_name='Dara')
    data.pop('save_address', None)
    client.post('/checkout', data=data)
    assert query(app, 'SELECT first_name FROM customer_addresses') == [('Sok',)]
