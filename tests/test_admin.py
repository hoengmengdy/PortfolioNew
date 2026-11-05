"""Admin dashboard tabs and one-tap order actions."""
from test_app import app, client, connect_db, login, payload, token  # noqa: F401  (pytest fixtures)
from test_shop import add_to_cart, order_form, query, sign_in, telegram_codes  # noqa: F401


def place_order(client, codes, method='bank', paid=True):
    sign_in(client, codes)
    add_to_cart(client, quantity=2)
    client.post('/checkout', data=order_form(client, payment_method=method))
    if paid:
        with connect_db(client.application) as connection:
            connection.execute("UPDATE orders SET payment_status='paid'")


def act(client, order_id, action, back=None):
    data = {'csrf_token': token(client, '/admin/orders'), 'action': action}
    if back:
        data['back'] = back
    return client.post(f'/admin/orders/{order_id}', data=data)


def test_admin_tabs(client, app, telegram_codes):
    place_order(client, telegram_codes)
    client.post('/api/contact', data=payload(client))
    with connect_db(app) as connection:
        connection.execute('UPDATE products SET stock=2 WHERE id=3')
    login(client)
    overview = client.get('/admin').text
    assert 'Orders to handle' in overview and 'Low stock' in overview and 'The Soft Touch' in overview
    assert '<b class="tab-badge">1</b>' in overview
    for view in ('orders', 'products', 'messages', 'retailers'):
        assert client.get(f'/admin/{view}').status_code == 200
    assert client.get('/admin/unknown').status_code == 404
    assert client.get('/admin/orders?status=bogus').status_code == 400
    assert 'Sok Dara' in client.get('/admin/orders?status=pending').text
    assert 'Sok Dara' not in client.get('/admin/orders?status=completed').text
    products = client.get('/admin/products').text
    assert 'id="product-3"' in products and 'Edit' in products
    assert 'Kigali Store' in client.get('/admin/retailers').text


def test_one_tap_order_actions(client, app, telegram_codes):
    place_order(client, telegram_codes, paid=False)
    # Checkout no longer offers cash on delivery, but older orders paid that way still exist.
    with connect_db(app) as connection:
        connection.execute("UPDATE orders SET payment_method='cod'")
    login(client)
    assert act(client, 1, 'confirm').location == '/admin/orders'
    assert query(app, 'SELECT status,payment_status FROM orders') == [('confirmed', 'unpaid')]
    act(client, 1, 'ship')
    # Delivering a cash-on-delivery order means the cash was collected.
    act(client, 1, 'complete', back='/admin?x=1')
    assert query(app, 'SELECT status,payment_status FROM orders') == [('completed', 'paid')]
    assert act(client, 1, 'explode').status_code == 400
    assert act(client, 1, 'confirm', back='https://evil.example').location == '/admin/orders'
    assert act(client, 99, 'confirm').status_code == 404


def test_cancel_reopen_and_mark_paid(client, app, telegram_codes):
    place_order(client, telegram_codes, method='bank')
    login(client)
    assert query(app, 'SELECT stock FROM products WHERE id=1') == [(23,)]
    act(client, 1, 'cancel')
    assert query(app, 'SELECT status FROM orders') == [('cancelled',)]
    assert query(app, 'SELECT stock FROM products WHERE id=1') == [(25,)]
    act(client, 1, 'reopen')
    assert query(app, 'SELECT status FROM orders') == [('pending',)]
    assert query(app, 'SELECT stock FROM products WHERE id=1') == [(23,)]
    page = client.get('/admin/orders').text
    assert 'value="paid"' in page and 'value="cancel"' in page
    act(client, 1, 'paid')
    assert query(app, 'SELECT payment_status FROM orders') == [('paid',)]


def test_message_quick_buttons_return_to_tab(client, app):
    client.post('/api/contact', data=payload(client))
    login(client)
    response = client.post('/admin/messages/1/status', data={'csrf_token': token(client, '/admin/messages'), 'status': 'archived', 'back': '/admin/messages?status=new'})
    assert response.location == '/admin/messages?status=new'
    assert query(app, 'SELECT status FROM messages') == [('archived',)]
    assert 'Mark unread' in client.get('/admin/messages').text


def test_unpaid_order_waits_outside_the_order_lists(client, app, telegram_codes):
    place_order(client, telegram_codes, paid=False)
    login(client)
    assert 'Sok Dara' not in client.get('/admin').text
    assert '<b class="tab-badge">' not in client.get('/admin').text
    for status in ('', '?status=pending'):
        assert 'Sok Dara' not in client.get(f'/admin/orders{status}').text
    waiting = client.get('/admin/orders?status=awaiting').text
    assert 'Sok Dara' in waiting and 'Awaiting payment (1)' in waiting
    # Nothing is lost: the reserved stock is released when the admin cancels it.
    assert query(app, 'SELECT stock FROM products WHERE id=1') == [(23,)]
    act(client, 1, 'cancel')
    assert query(app, 'SELECT stock FROM products WHERE id=1') == [(25,)]
    assert 'Sok Dara' in client.get('/admin/orders?status=cancelled').text
    assert 'Sok Dara' not in client.get('/admin/orders?status=awaiting').text


def test_order_reaches_admin_when_paid_or_payment_reported(client, app, telegram_codes):
    place_order(client, telegram_codes, paid=False)
    order_token = query(app, 'SELECT token FROM orders')[0][0]
    csrf = token(client, f'/orders/{order_token}')
    client.post(f'/orders/{order_token}/payment', data={'csrf_token': csrf, 'reference': 'ABA-778899'})
    login(client)
    assert 'Sok Dara' in client.get('/admin').text
    assert 'Sok Dara' in client.get('/admin/orders?status=payment').text
    assert 'Sok Dara' not in client.get('/admin/orders?status=awaiting').text


def test_admin_can_mark_a_waiting_order_paid(client, app, telegram_codes):
    place_order(client, telegram_codes, paid=False)
    login(client)
    act(client, 1, 'paid')
    assert 'Sok Dara' in client.get('/admin/orders?status=pending').text
    assert 'Sok Dara' not in client.get('/admin/orders?status=awaiting').text


def test_cash_on_delivery_orders_are_never_held_back(client, app, telegram_codes):
    place_order(client, telegram_codes, paid=False)
    with connect_db(app) as connection:
        connection.execute("UPDATE orders SET payment_method='cod'")
    login(client)
    assert 'Sok Dara' in client.get('/admin/orders?status=pending').text
