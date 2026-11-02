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

## Pages and behavior

| Route | Purpose |
| --- | --- |
| `/` | Full home page, collection inquiry links, features, image lightbox, partnerships |
| `/about` | Story, mission, vision, quality, sustainability approach |
| `/retailers?country=Rwanda&city=Kigali` | Server-rendered country/city filtering and Google Maps directions |
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
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m pip check
node --check static/js/main.js
.\.venv\Scripts\python tests/http_smoke.py
```

Tests use temporary databases and cover all public pages in both languages, language persistence, safe redirects, contact validation and persistence, CSRF protection, stored HTML escaping, rate limits, admin access/logout/status updates, CLI account creation, country/city search, and retailer creation/edit/deletion. The application was also started and checked over real HTTP. Native browser automation was stopped by the environment because it could not determine the Chrome URL with enough confidence; desktop/mobile visual browser QA remains unverified.

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
static/images/          Local optimized images and favicon
static/fonts/           Local typefaces and licenses
static/webfonts/        Font Awesome WOFF2 files
translations/           English and Khmer JSON catalogs
tests/test_app.py       Backend integration tests
ASSETS.md               Image sources and licenses
```

## UI refinements

The public pages and admin dashboard share one light-blue design system in `static/css/style.css`: consistent navigation, readable Inter/Noto Sans Khmer typography, standard form controls, and compact mobile layouts. The home page removes repeated introductory sections. The admin dashboard includes direct links to inquiries and retailers. Content stays visible without scroll-triggered reveals.
#   e m p r e s s  
 