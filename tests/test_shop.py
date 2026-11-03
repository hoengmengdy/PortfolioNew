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
    data = dict(csrf_token=token(client, '/checkout'), name='Sok Dara', email='', address='Street 51, BKK1', city='Phnom Penh', note='', payment_method='cod')
    data.update(changes)
    return data


def query(app, sql, *args):
    with connect_db(app) as connection:
        return connection.execute(sql, args).fetchall()


def test_shop_cart_and_cash_on_delivery_checkout(client, app, telegram_codes):
    assert '/account/login' in client.get('/checkout').location
    shop = client.get('/shop').text
    assert '$18.00' in shop and 'Add to cart' in shop
    assert add_to_cart(client).status_code == 303
    assert add_to_cart(client, product_id=999).status_code == 404
    cart = client.get('/cart').text
    assert '$36.00' in cart and '$37.50' in cart
    assert 'class="cart-count" aria-hidden="true">2<' in cart
    sign_in(client, telegram_codes)
    response = client.post('/checkout', data=order_form(client))
    assert response.status_code == 303
    page = client.get(response.location).text
    assert 'Cash on delivery' in page and '$37.50' in page and 'Sok Dara' in page
    assert query(app, 'SELECT total_cents,payment_method,status,payment_status,phone,customer_id FROM orders') == [(3750, 'cod', 'pending', 'unpaid', '+85512345678', 1)]
    assert query(app, 'SELECT name,unit_cents,quantity FROM order_items') == [('The Daily Glow', 1800, 2)]
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


def test_checkout_validation(client, app, telegram_codes):
    sign_in(client, telegram_codes)
    add_to_cart(client)
    response = client.post('/checkout', data=order_form(client, name='A', phone='abc', address='x', email='bad', payment_method='crypto'))
    assert response.status_code == 422
    for message in ['delivery address', 'valid email', 'payment method']:
        assert message in response.text
    assert 'value="A"' in response.text
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
