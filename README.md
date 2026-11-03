# Empress Cambodia · Flask skincare website

A complete Flask/SQLite implementation inspired by the page flow of [Skin Paradise](https://skinparadise.rw/). Uses original concept branding, copy, and its own visual treatment. It is not affiliated with the reference company. All files live directly in the requested project directory.

## Run on Windows

Python 3.12+ is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env: set SECRET_KEY to a long, cryptographically random value.
.\.venv\Scripts\python index.py
```

Open http://127.0.0.1:5050. `python app.py` also works. Debug mode is disabled. The database and schema are created automatically on first start. Images, icons, and fonts are bundled; the public site does not depend on CDN access.

## Administrator access

Open http://127.0.0.1:5050/admin. This installed workspace has a generated local administrator account; its username and unique password are in `.admin-credentials.txt` in the project root. That file is ignored by Git. Keep it private and remove it once the password is stored in your password manager. There is no default password in the source code.

For a fresh installation, create an account with the interactive command:

```powershell
.\.venv\Scripts\python -m flask --app app create-admin
```

The password prompt is hidden, requires confirmation, and requires at least 12 characters. Passwords are stored as Werkzeug scrypt hashes. The dashboard supports:

- Inquiry counts, filters, expandable messages, and status changes (new/read/archived).
- Email reply links that open your mail application; the website does not send email.
- Adding, editing, and deleting retailer listings.
- CSRF-protected sign-in/out, rate-limited login, and 30-minute sessions.

The inbox shows the latest 200 inquiries per filter. Archived records remain in the database. Dates are displayed in UTC. Protect and back up the database as private customer data; choose an appropriate retention policy. Handle privacy removal requests by deleting the requested record through a controlled database maintenance procedure.

## Shop, cart, and payment

Customers browse `/shop`, add items to a session cart (`/cart`), and check out at `/checkout` with their name, phone, delivery address, and payment method. Each order gets a private, unguessable link (`/orders/<token>`) showing its status and payment instructions.

Delivery address: first and last name, a phone number after a fixed `+855` prefix, then **capital/province → district/khan → commune/sangkat** lists (each choice fills the next one) and the house number and street. The server checks that the three choices belong together. The order stores the address as text in the customer's language, for example `House 12, Street 51, Tonle Basak, Chamkar Mon` with `Phnom Penh` as the city. **Set as my default address** (ticked by default) saves it in `customer_addresses`, and the next checkout is filled in from it.

The list of 25 provinces, 210 districts and 1,652 communes is `static/data/cambodia.json`, built by `python build_locations.py <folder>` from the YAML files of the [pumi](https://github.com/dwilkie/pumi) gazetteer (MIT licence, `static/data/PUMI-LICENSE.txt`). Re-run it if the government changes the boundaries.

Payment methods:

- **ABA PayWay** (ABA PAY, KHQR from any Cambodian bank app, Visa/Mastercard) appears first when `PAYWAY_MERCHANT_ID` and `PAYWAY_API_KEY` are set. After placing the order, the customer is sent to ABA's secure checkout page, and card details never touch this site. When they return to the order page, the site asks PayWay (Check Transaction API) whether the payment was approved for the full amount, and only then marks the order **Paid**. PayWay's server notice to `/payway/callback` triggers the same check. That notice only reaches a public HTTPS domain that is whitelisted in your PayWay profile. Start with sandbox keys from https://sandbox.payway.com.kh/register-sandbox/, then set `PAYWAY_BASE_URL=https://checkout.payway.com.kh` with your live keys from ABA (paywaysales@ababank.com).
- **Cash on delivery** is not offered at checkout. Older cash-on-delivery orders still show and can be completed in the admin.
- **Bank transfer / KHQR** (ABA, ACLEDA, Wing, or any bank app) appears only when `PAYMENT_ACCOUNT_NUMBER` is set in `.env`. The order page shows the bank, account name, number, amount, and memo `EMP-<order id>`. The customer enters their transaction reference and the payment becomes *Awaiting confirmation*. After checking your bank app, mark it *Paid* in the admin dashboard.

`DELIVERY_FEE` (for example `1.50`) is added to every order, and `CURRENCY_SYMBOL` controls price display. Stock is reserved when an order is placed. It cannot oversell, and it is returned when an admin cancels the order.

The admin dashboard has **Orders** (change order and payment status, view items, address, and reference) and **Products** (name and description in English/Khmer, price, stock, image, and shop visibility). Three starter products with **example prices** are created on first start. Set your real prices and stock before taking orders.

No card payments are processed and no customer data is sent to a payment provider. Online card or KHQR gateways such as ABA PayWay or Stripe need a merchant account and API keys. They can be added later as another payment method.

## Customer accounts (sign in with Telegram)

Customers must sign in before checkout. They enter their phone number (local numbers such as `012 345 678` are treated as Cambodian, `+855`). A 6-digit code is sent to their Telegram, by your own free bot or by the paid Telegram Gateway, and they type it in to sign in. There are no passwords. `/account` lists the customer's own orders.

### Free setup: Telegram bot (recommended)

1. In Telegram, open **@BotFather**, send `/newbot`, choose a name (for example "Empress Cambodia") and a username ending in `bot` (for example `EmpressShopBot`).
2. Copy the token BotFather gives you into `.env`: `TELEGRAM_BOT_TOKEN=123456789:AA...`
3. Start the site with `python index.py`. The log shows `Telegram bot @YourBot is running`.

Sign-in flow: the customer enters their phone number and taps **Open Telegram**, presses **Start**, and then taps **Share my phone number**. Telegram provides their verified number. The bot sends the code only if that number matches the one typed on the website, so nobody can receive a code for someone else's number. Next time, the code arrives straight away without these steps.

The bot uses long polling, so it works on a local computer without a public address. When the website is served by waitress, run the bot as a second process with `python -m flask --app app telegram-bot`. Only one copy of the bot may run at a time.

### Paid alternative: Telegram Gateway

Leave `TELEGRAM_BOT_TOKEN` empty and set `TELEGRAM_GATEWAY_TOKEN` from https://gateway.telegram.org. Codes then arrive from Telegram's official "Verification Codes" account with no bot step. This costs a small fee per code.

For local testing without a token, set `TELEGRAM_DEV_MODE=true`. Codes are then written to the server log (`server-5050-error.log`) instead of being sent. Never enable dev mode on a public site.

Codes expire after 5 minutes and allow 5 wrong attempts. Only a keyed hash of each code is stored. A number can request a new code once per minute and 5 times per hour, and each IP address can receive 5 codes per minute and 20 per hour. Only codes actually sent count, so typos and retries never lock anyone out. In test mode the code is also shown on the sign-in page.

## Pages and behavior

| Route | Purpose |
| --- | --- |
| `/` | Full home page, collection inquiry links, features, image lightbox, partnerships |
| `/about` | Story, mission, vision, quality, sustainability approach |
| `/retailers?country=Rwanda&city=Kigali` | Server-rendered country/city filtering and Google Maps directions |
| `/shop`, `/cart`, `/checkout` | Product catalogue, session cart, delivery and payment form |
| `/account/login`, `/account` | Phone + Telegram code sign-in, customer order history |
| `/orders/<token>` | Private order status page, bank-transfer reference submission |
| `/contact` | Accessible contact form, field validation, errors, success notification |
| `/api/contact` | POST form or JSON; validates and saves inquiry to SQLite |
| `/set-language/<en\|km>` | Language preference, safe local redirect, one-year preference cookie |
| `/admin/login` | Administrator authentication |
| `/admin` | Protected inquiry and retailer management |
| `/admin/logout` | POST sign-out |

The form works without JavaScript. JavaScript adds mobile navigation, password visibility control, a keyboard-accessible native dialog gallery, and retailer deletion confirmation. Reduced-motion preferences are honored. The language selector works on all pages, including admin and validation errors. JSON catalogs are in `translations/`; edit `build_translations.py` and run it to regenerate both together. Khmer has a bundled Khmer font. Have fluent speakers review translated copy before a public launch.

JSON requests require a CSRF token from the session's contact form, sent using `X-CSRFToken`, and the same session cookie. Success is HTTP 201; validation errors are HTTP 422. Normal forms redirect after success to prevent accidental resubmission. Limits are five contact submissions per minute and 30 per hour per remote address; login allows ten attempts per minute and 50 per hour. No automated email or third-party data transmission occurs when a contact inquiry is saved.

## Content setup

This is an independently branded concept, not an authorized copy of Skin Paradise. Product collection names and photography are illustrative. Do not treat them as a verified commercial catalog. Claims about certifications, testing, ingredient formulations, or stock availability are intentionally not invented.

The local database contains three **explicitly marked example retailers**. Replace or delete those in the admin dashboard before launch. On fresh installs, an empty directory works normally; optional sample entries can be added with:

```powershell
.\.venv\Scripts\python -m flask --app app seed-demo
```

Set `CONTACT_EMAIL` and `CONTACT_PHONE` in `.env` to your actual business contacts. Otherwise the site directs visitors to the functioning inquiry form. Update concept copy and product availability with your authorized business details before publishing.

## Verification

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m pip check
node --check static/js/main.js
.\.venv\Scripts\python tests/http_smoke.py
```

Tests use temporary databases and cover all public pages in both languages, language persistence, safe redirects, contact validation and persistence, CSRF protection, stored HTML escaping, rate limits, admin access/logout/status updates, CLI account creation, country/city search, and retailer creation/edit/deletion. The application was also started and checked over real HTTP. Native browser automation was stopped by the environment because it could not determine the Chrome URL with enough confidence; desktop/mobile visual browser QA remains unverified.

## Deploy on Vercel (empresscambodia.vercel.app)

Vercel cannot save files, so the live site stores its data in Postgres. On your computer it keeps using `database.db` (SQLite). The same code handles both. When `DATABASE_URL` is set, Postgres is used.

1. **Database:** in the Vercel project, open **Storage → Create Database → Neon (Postgres)** and connect it to this project. Vercel then sets `DATABASE_URL` automatically. Tables and starter products are created on the first visit.
2. **Environment variables** (Project → Settings → Environment Variables, for Production):

   | Name | Value |
   | --- | --- |
   | `SECRET_KEY` | a long random value (`python -c "import secrets; print(secrets.token_hex(32))"`) |
   | `ADMIN_USERNAME` / `ADMIN_PASSWORD` | the first admin account (password at least 12 characters), created on start-up |
   | `TELEGRAM_BOT_TOKEN` | the same bot token as in `.env` |
   | `PAYWAY_MERCHANT_ID`, `PAYWAY_API_KEY`, `PAYWAY_BASE_URL` | ABA PayWay keys (sandbox or live) |
   | optional | `DELIVERY_FEE`, `CONTACT_EMAIL`, `CONTACT_PHONE`, `CONTACT_ADDRESS`, `BUSINESS_HOURS`, `INSTAGRAM_URL`, bank-transfer settings |

3. **Deploy:** push to the GitHub repository connected to Vercel, or redeploy after changing variables.
4. **Telegram bot:** Vercel cannot run the bot in the background, so connect it with a webhook (once, from this computer):

   ```powershell
   .\.venv\Scripts\python -m flask --app app telegram-webhook https://empresscambodia.vercel.app
   ```

   After this, the live site owns the bot, and `python index.py` locally no longer polls it. Use a second test bot locally, or run `telegram-webhook --delete` to take it back.
5. **ABA PayWay:** add `https://empresscambodia.vercel.app` to the allowed domains in your PayWay profile so the payment notice reaches `/payway/callback`.

On Vercel, cookies are sent over HTTPS only, and forwarded `https` addresses are trusted, so links and PayWay return URLs use the public domain. Rate limits are kept per server instance.

## Production deployment

Serve the app using a WSGI server behind an HTTPS reverse proxy:

```powershell
.\.venv\Scripts\python -m waitress --listen=127.0.0.1:5050 app:app
```

Set a unique `SECRET_KEY`, set `COOKIE_SECURE=true` when using HTTPS, keep `.env`, `.secret_key`, `.admin-credentials.txt`, and `database.db*` out of source control and public directories, and restrict filesystem access to the service user. The auto-generated `.secret_key` is a persistent local-development fallback; use an environment-managed secret in production. Back up SQLite using its backup API rather than copying a live database without its WAL. SQLite is appropriate for a small site with modest write volume.

The default limiter storage is process memory and is suitable for a single-process local server. For multiple processes or durable rate limits, install the Redis extra (`python -m pip install "Flask-Limiter[redis]"`) and configure `RATELIMIT_STORAGE_URI=redis://...`. If behind a proxy, configure trusted forwarding only for the known proxy count; do not trust arbitrary forwarded IP headers. Configure HTTPS, domain/host restrictions, monitoring, retention, backups, and verified business content for the actual hosting environment before launch. No public deployment is performed by this project.

## Project files

```text
app.py                  Application factory, routes, database, CLI
index.py                IDE-friendly launch entry point
config.py               Environment configuration
requirements.txt        Runtime and verification dependencies
requirements.lock.txt   Exact installed versions
database.db             Local SQLite data (ignored by Git)
templates/              Shared layout and all public/admin pages
static/css/             Custom responsive styling and Font Awesome
static/js/main.js       Progressive enhancement
static/data/            Cambodian provinces, districts and communes (build_locations.py)
locations.py            Address lookup and validation
static/images/          Local optimized images and favicon
static/fonts/           Local typefaces and licenses
static/webfonts/        Font Awesome WOFF2 files
translations/           English and Khmer JSON catalogs
tests/test_app.py       Backend integration tests
ASSETS.md               Image sources and licenses
```

## UI refinements

The public pages and admin dashboard share one light-blue design system in `static/css/style.css`: consistent navigation, readable Inter/Noto Sans Khmer typography, standard form controls, and compact mobile layouts. The home page removes repeated introductory sections. The admin dashboard includes direct links to inquiries and retailers. Public pages have strong motion: the hero text slides in out of a blur while the photo zooms and slowly drifts, and the Contact button pulses. Headings slide in from the side as you scroll, cards jump up with a bounce, steps flip up, gallery photos spin in, and story photos come from alternating sides. Product cards tilt in 3D towards the mouse, buttons get a light sweep and a press ripple, and a progress bar along the top shows how far you have scrolled. Only content below the first screen is hidden before it is revealed. Everything stays visible without JavaScript, and all motion is off for visitors who prefer reduced motion. Bootstrap is not used: it has no scroll or entrance animations of its own, and its base styles would override this design. All motion is in `style.css` and `main.js`.
