"""One small database interface for SQLite (local development) and Postgres (production, e.g. Vercel + Neon).

Application SQL is written once with `?` placeholders in the subset both databases understand. Only the schema
and transaction start differ, and those live here.
"""
import re
import sqlite3
import threading
import time

try:
    import psycopg
    ERRORS = (sqlite3.Error, psycopg.Error)
except ImportError:  # SQLite-only installs do not need the Postgres driver.
    ERRORS = (sqlite3.Error,)

# Tables whose primary key is an `id` column; inserts into them report the new id like sqlite3's lastrowid.
ID_TABLES = {'messages', 'admins', 'retailers', 'products', 'orders', 'order_items', 'customers', 'login_codes', 'product_photos'}

SQLITE_SCHEMA = '''
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
    CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, name_km TEXT NOT NULL DEFAULT '',
        description TEXT NOT NULL DEFAULT '', description_km TEXT NOT NULL DEFAULT '',
        price_cents INTEGER NOT NULL CHECK (price_cents >= 0), stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
        image TEXT NOT NULL DEFAULT 'hero.webp', active INTEGER NOT NULL DEFAULT 1);
    CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, phone TEXT NOT NULL UNIQUE, name TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')));
    CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, token TEXT NOT NULL UNIQUE, customer_id INTEGER REFERENCES customers(id),
        name TEXT NOT NULL, phone TEXT NOT NULL, email TEXT NOT NULL DEFAULT '', address TEXT NOT NULL, city TEXT NOT NULL,
        note TEXT NOT NULL DEFAULT '', payment_method TEXT NOT NULL, payment_status TEXT NOT NULL DEFAULT 'unpaid',
        payment_reference TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'pending',
        subtotal_cents INTEGER NOT NULL, delivery_cents INTEGER NOT NULL, total_cents INTEGER NOT NULL,
        language TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')));
    CREATE TABLE IF NOT EXISTS order_items (id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
        product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
        name TEXT NOT NULL, unit_cents INTEGER NOT NULL, quantity INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS login_codes (id INTEGER PRIMARY KEY, phone TEXT NOT NULL, code_hash TEXT NOT NULL,
        ip TEXT NOT NULL DEFAULT '', start_token TEXT NOT NULL DEFAULT '', chat_id INTEGER,
        attempts INTEGER NOT NULL DEFAULT 0, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL);
    CREATE INDEX IF NOT EXISTS login_codes_phone ON login_codes(phone, created_at);
    CREATE TABLE IF NOT EXISTS telegram_chats (phone TEXT PRIMARY KEY, chat_id INTEGER NOT NULL, updated_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS payway_transactions (tran_id TEXT PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
        amount_cents INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending', apv TEXT NOT NULL DEFAULT '', created_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS customer_addresses (customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
        first_name TEXT NOT NULL, last_name TEXT NOT NULL, phone TEXT NOT NULL, province TEXT NOT NULL, district TEXT NOT NULL,
        commune TEXT NOT NULL, street TEXT NOT NULL, PRIMARY KEY(customer_id));
    CREATE TABLE IF NOT EXISTS product_photos (id INTEGER PRIMARY KEY AUTOINCREMENT, data BLOB NOT NULL, created_at INTEGER NOT NULL);
'''
# Columns added after the first release; older local databases get them on start-up.
SQLITE_MIGRATIONS = [('orders', 'customer_id', 'INTEGER REFERENCES customers(id)'), ('login_codes', 'ip', "TEXT NOT NULL DEFAULT ''"),
                     ('login_codes', 'start_token', "TEXT NOT NULL DEFAULT ''"), ('login_codes', 'chat_id', 'INTEGER')]

PG_NOW = '''(to_char(now() AT TIME ZONE 'utc', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'))'''
POSTGRES_SCHEMA = (SQLITE_SCHEMA
                   .replace('PRAGMA journal_mode=WAL;', '')
                   # Postgres sequences never reuse ids, so photo URLs can be cached forever on both databases.
                   .replace(' AUTOINCREMENT', '').replace('BLOB', 'BYTEA')
                   .replace('id INTEGER PRIMARY KEY', 'id BIGSERIAL PRIMARY KEY')
                   .replace("(strftime('%Y-%m-%dT%H:%M:%SZ','now'))", PG_NOW)
                   # Telegram chat ids and Unix times do not fit in 32 bits.
                   .replace('chat_id INTEGER', 'chat_id BIGINT')
                   .replace('created_at INTEGER', 'created_at BIGINT').replace('expires_at INTEGER', 'expires_at BIGINT')
                   .replace('updated_at INTEGER', 'updated_at BIGINT')
                   .replace('customer_id INTEGER', 'customer_id BIGINT').replace('order_id INTEGER', 'order_id BIGINT')
                   .replace('product_id INTEGER', 'product_id BIGINT'))
POSTGRES_SCHEMA += 'CREATE INDEX IF NOT EXISTS login_codes_start ON login_codes(start_token);\n'


class Row(tuple):
    """A result row usable by position, by column name and with dict(), like sqlite3.Row."""

    def __new__(cls, values, names):
        row = super().__new__(cls, values)
        row._index = {name: i for i, name in enumerate(names)}
        return row

    def __getitem__(self, key):
        if isinstance(key, str):
            return tuple.__getitem__(self, self._index[key])
        return tuple.__getitem__(self, key)

    def keys(self):
        return list(self._index)


class PostgresCursor:
    def __init__(self, cursor, lastrowid=None):
        self._cursor, self.lastrowid = cursor, lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def fetchone(self):
        return self._cursor.fetchone() if self._cursor.description else None

    def fetchall(self):
        return self._cursor.fetchall() if self._cursor.description else []

    def __iter__(self):
        return iter(self.fetchall())


class PostgresConnection:
    """Wraps a psycopg connection with the small part of the sqlite3 API the app uses."""
    dialect = 'postgres'

    def __init__(self, url):
        def row_factory(cursor):
            names = [column.name for column in cursor.description] if cursor.description else []
            return lambda values: Row(values, names)

        # Automatic server-side prepared statements are disabled: they do not survive Neon's connection pooler reliably.
        # GSS encryption is never used by hosted Postgres; skipping its negotiation shortens every new connection.
        self._connection = psycopg.connect(url, row_factory=row_factory, connect_timeout=10, prepare_threshold=None, gssencmode='disable')
        self.url, self.last_used = url, time.monotonic()

    def usable(self):
        """True when this connection can serve another request; checks the server after a quiet minute."""
        if self._connection.closed:
            return False
        if time.monotonic() - self.last_used > 60:
            try:
                self._connection.execute('SELECT 1')
                self._connection.rollback()
            except psycopg.Error:
                self.close()
                return False
        return True

    def release(self):
        """End the request: discard any unfinished transaction and return the connection to the shared pool."""
        try:
            self._connection.rollback()
        except psycopg.Error:
            self.close()
            return
        self.last_used = time.monotonic()
        with _pool_lock:
            idle = _pool.setdefault(self.url, [])
            if len(idle) < POOL_SIZE:
                idle.append(self)
                return
        self.close()

    @staticmethod
    def _translate(sql):
        # psycopg uses %s placeholders, so literal percent signs must be doubled first.
        return sql.replace('%', '%%').replace('?', '%s')

    def execute(self, sql, params=()):
        if sql.strip().upper() == 'BEGIN IMMEDIATE':
            # psycopg already runs every statement inside a transaction until commit or rollback.
            return PostgresCursor(self._connection.cursor())
        insert = re.match(r'\s*INSERT\s+INTO\s+(\w+)', sql, re.IGNORECASE)
        wants_id = insert and insert.group(1).lower() in ID_TABLES and 'RETURNING' not in sql.upper()
        cursor = self._connection.execute(self._translate(sql) + (' RETURNING id' if wants_id else ''), tuple(params))
        # ON CONFLICT DO NOTHING returns no row when nothing was inserted.
        row = cursor.fetchone() if wants_id else None
        return PostgresCursor(cursor, row[0] if row else None)

    def executemany(self, sql, rows):
        with self._connection.cursor() as cursor:
            cursor.executemany(self._translate(sql), [tuple(row) for row in rows])

    def executescript(self, script):
        self._connection.execute(script)

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()


# Idle Postgres connections shared by all threads of this process. Hosts such as Vercel may run each request on a
# new thread, so connections are pooled per process rather than per thread.
POOL_SIZE = 4
_pool = {}
_pool_lock = threading.Lock()


def connect(config, reuse=False):
    """Open a connection: Postgres when DATABASE_URL is set, otherwise the local SQLite file.

    With reuse=True a Postgres connection is taken from the process pool when one is idle, saving the TLS and login
    round trips (the slowest part of a request on serverless hosts). Give it back with release() instead of close().
    """
    url = config.get('DATABASE_URL')
    if url:
        while reuse:
            with _pool_lock:
                idle = _pool.get(url)
                connection = idle.pop() if idle else None
            if connection is None:
                break
            if connection.usable():
                return connection
        return PostgresConnection(url)
    connection = sqlite3.connect(config['DATABASE'], timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys=ON')
    return connection


def is_postgres(connection):
    return getattr(connection, 'dialect', 'sqlite') == 'postgres'


def create_schema(connection):
    if is_postgres(connection):
        # Skip the DDL on every cold start once the newest table exists (update this name when adding tables).
        if connection.execute("SELECT to_regclass('product_photos')").fetchone()[0]:
            return
        # Concurrent cold starts on Vercel may run this at the same time; serialise them with an advisory lock.
        connection.execute('SELECT pg_advisory_xact_lock(4242)')
        connection.executescript(POSTGRES_SCHEMA)
        return
    connection.executescript(SQLITE_SCHEMA)
    for table, column, definition in SQLITE_MIGRATIONS:
        if column not in {row['name'] for row in connection.execute(f'PRAGMA table_info({table})')}:
            connection.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
    connection.execute('CREATE INDEX IF NOT EXISTS login_codes_start ON login_codes(start_token)')
