# Qubaa Mosque — Announcements (Django + MySQL)

A small bilingual website where a mosque publishes its needs — for people or for
the mosque itself — and visitors browse them and get in touch to help.

- **Public site** in Arabic (default, RTL) and English (LTR), under `/ar/` and `/en/`.
- **Staff dashboard** at `/ar/dashboard/` and `/en/dashboard/` — a dedicated,
  bilingual workspace for the mosque team, separate from the Django admin.
- **Django admin** (`/admin/`) kept for accounts and advanced settings only.
- **Deployable to Render** with `render.yaml`, gunicorn and WhiteNoise.
- **MySQL in production**, SQLite automatically for local development.

---

## 1. What the site does

| Area | Details |
| --- | --- |
| Home | Hero, counters (published / open / for people / for the mosque), latest announcements, how it works, call to action. |
| Announcements | Search (title, description, beneficiary, city, country), filters by type, category and status, pagination. |
| Announcement detail | Full description, beneficiary, location, fundraising progress, contact card, share buttons, related announcements. |
| About | Mission, values, how to help, contact details. |
| Dashboard | Staff-only workspace: overview, search and filters, create/edit, publish and hide, bulk actions, password change. Arabic and English. |
| Django admin | Accounts, permissions and advanced settings. Branded, with bilingual fields and image preview. |

Announcements are **bilingual**: each has `*_ar` and `*_en` fields, and the site
automatically falls back to the other language when one is empty.

Money is stored as `goal_amount` / `raised_amount` plus a `currency`; a
progress bar, percentage and remaining amount are computed automatically.

There are **no file uploads** (Render's disk is ephemeral). Announcements use an
external `image_url` instead, and the mosque keeps full-size photos wherever it
already stores them.

---

## 2. Local development

Requirements: Python 3.10+ (3.12 recommended), and MySQL 8 only if you want to
test the production database engine.

```powershell
# 1. Create and activate a virtual environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your local configuration
Copy-Item .env.example .env

# 4. Create the database tables
python manage.py migrate

# 5. Create the administrator account (uses ADMIN_EMAIL / ADMIN_PASSWORD)
python manage.py ensure_admin

# 6. Optional: six bilingual demo announcements
python manage.py seed_demo

# 7. Run the site
python manage.py runserver
```

Open <http://127.0.0.1:8000/> — you are redirected to `/ar/`.
The staff dashboard is at <http://127.0.0.1:8000/ar/dashboard/>,
and the Django admin is at <http://127.0.0.1:8000/admin/>.

The default `.env.example` credentials are `admin@example.org` /
`ChangeMe-12345!`. Change them before deploying anything public.

> On Windows, `gunicorn` does not run; use `runserver` locally. Gunicorn is only
> used on Render's Linux environment.

### Using MySQL locally

SQLite is used whenever `DATABASE_URL` is empty. To test MySQL:

```powershell
docker compose up -d          # MySQL 8.4 on 127.0.0.1:3307
```

Then set in `.env`:

```dotenv
DATABASE_URL=mysql://qubaa:qubaa@127.0.0.1:3307/qubaa?charset=utf8mb4
```

and run `python manage.py migrate` again. Remove the line to go back to SQLite.
(The data is not copied between the two databases.)

No Docker? Install MySQL 8 locally and create a `qubaa` database, then point
`DATABASE_URL` at it.

---

## 3. Environment variables

All settings are read from environment variables (and from `.env` locally).

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `SECRET_KEY` | production | insecure dev key | Django secret. Render generates one. |
| `DEBUG` | no | `False` | `True` locally only. |
| `ALLOWED_HOSTS` | no | `localhost,127.0.0.1,[::1]` | Comma-separated extra hosts. `RENDER_EXTERNAL_HOSTNAME` is added automatically. |
| `CSRF_TRUSTED_ORIGINS` | no | — | Comma-separated extra origins, e.g. `https://example.org`. |
| `DATABASE_URL` | production | SQLite | `mysql://user:password@host:3306/database?charset=utf8mb4` |
| `DB_SSL_CA` | if required | — | Path to the provider's CA certificate file. |
| `DB_SSL_VERIFY` | no | `True` | Set `False` to accept a TLS certificate that does not match the host. |
| `DB_PATH` | no | `<project>/db.sqlite3` | Where the SQLite file lives. On Render, point it at a persistent disk (e.g. `/data/db.sqlite3`). |
| `DB_CONN_MAX_AGE` | no | `60` | Persistent connections, in seconds. |
| `ADMIN_EMAIL` | first deploy | — | Administrator login (used as username). |
| `ADMIN_PASSWORD` | first deploy | — | Administrator password, validated by Django. |
| `ADMIN_NAME` | no | `Administrator` | Display name of the administrator. |
| `ADMIN_RESET_PASSWORD` | no | `False` | Set `True` once to reset an existing password from `ADMIN_PASSWORD`. |
| `SITE_NAME_AR` / `SITE_NAME_EN` | no | `مسجد قباء` / `Qubaa Mosque` | Mosque name in each language. |
| `SITE_TAGLINE_AR` / `SITE_TAGLINE_EN` | no | `نخدم مجتمعنا` / `Serving our community` | Tagline. |
| `CONTACT_EMAIL`, `CONTACT_PHONE` | no | — | Shown in the footer, detail pages and CTA. |
| `CONTACT_ADDRESS_AR`, `CONTACT_ADDRESS_EN` | no | — | Address in each language. |
| `DEFAULT_CURRENCY` | no | `EUR` | Default currency for new announcements. |
| `SECURE_SSL_REDIRECT` | no | `False` | Redirect HTTP to HTTPS (Render already redirects). |
| `SECURE_HSTS_SECONDS` | no | `0` | Enable HSTS once HTTPS is confirmed stable. |
| `LOG_LEVEL` | no | `INFO` | Logging level. |

Secrets are never committed: `.env` is ignored, and `render.yaml` asks Render
for the secret values instead of storing them.

---

## 4. Deploying to Render

Render does **not** offer managed MySQL. The web service runs on Render, and the
database lives with an external MySQL provider (or your own server).

### Step 1 — Create the MySQL database

Any MySQL 8-compatible provider works, for example:

- Clever Cloud (MySQL add-on)
- Aiven for MySQL
- Railway MySQL
- PlanetScale (MySQL-compatible; use the connection string it gives you)
- Your own server with MySQL 8

Create a database (for example `qubaa`) and a user with full rights on it. Make
sure the provider allows connections from outside (Render's IPs are dynamic, so
IP allow-listing usually has to be open or you need a proxy). Copy the
connection URL:

```text
mysql://USER:PASSWORD@HOST:3306/qubaa?charset=utf8mb4
```

If the provider requires TLS, download its CA certificate and set `DB_SSL_CA` to
a path inside the repository (commit the certificate file) or set
`DB_SSL_VERIFY=False` when the certificate cannot be verified.

### Step 2 — Push the project to GitHub

```powershell
git init
git add .
git commit -m "Qubaa mosque announcements"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

`django.mo` (the compiled Arabic catalog) **must be committed** — Render has no
`msgfmt` binary. `build.sh` also recompiles it with the project's pure-Python
script, so translations are never missing.

### Step 3 — Create the Render Blueprint

1. In Render: **New → Blueprint**, select the repository.
2. Render reads `render.yaml` and asks for the values marked `sync: false`:
   - `DATABASE_URL` — the URL from step 1
   - `ADMIN_EMAIL`, `ADMIN_PASSWORD` — the first administrator
   - `DB_SSL_CA` — only if your provider needs a CA file
   - contact details — optional
3. Apply. Render runs:

   ```text
   bash build.sh
   gunicorn config.wsgi:application --bind 0.0.0.0:$PORT ...
   ```

   `build.sh` installs dependencies, compiles translations, collects static
   files, migrates the database and creates the administrator.
4. Wait for the health check at `/healthz/` to turn green, then open
   `https://<service>.onrender.com/` (it redirects to `/ar/`).

`RENDER_EXTERNAL_HOSTNAME` is injected automatically and added to
`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, so login and forms work without
extra configuration. Add a custom domain in Render if needed, then add it to
`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` as well.

### Step 4 — First login

Open `https://<service>.onrender.com/ar/dashboard/` and sign in with
`ADMIN_EMAIL` / `ADMIN_PASSWORD`, then create your announcements. Use `/admin/`
only to add staff accounts and change settings.

> Free Render services spin down after inactivity; the first request after a
> pause can take up to a minute. The external database is unaffected.

---

## 5. Day-to-day administration

### The staff dashboard

The mosque team works in the dashboard, not in the Django admin:

```text
https://<service>.onrender.com/ar/dashboard/     Arabic (default, RTL)
https://<service>.onrender.com/en/dashboard/     English (LTR)
```

Signing in redirects to the overview, with counters, the latest updates,
fundraising totals per currency, and needs by type.

| Page | What it does |
| --- | --- |
| **Overview** | Totals, drafts, open needs, fundraising progress, recent changes. |
| **Announcements** | Search and filter by type, category, status and visibility; bulk publish/hide/fulfil/reopen. |
| **New / Edit** | Sectioned bilingual form, image preview, progress, contact details, publish switch. |
| **Password** | Staff can change their own password. |

How the dashboard behaves:

- **Login**: any `is_staff` account can sign in. If an anonymous visitor opens a
  dashboard page, they are sent to the dashboard login and returned afterwards.
- **Non-staff accounts** receive a `403` page: creating a user is not enough,
  `is_staff` must be checked.
- **Deletion is restricted to superusers**; all staff can create, edit, publish,
  hide and change the status.
- **Languages**: the same interface is available in Arabic and English. The
  switcher in the top bar keeps you on the same page. Arabic is the default.
- **Drafts**: an unpublished announcement never appears on the public site, even
  when its status is `open`.
- **No file uploads**: paste an `https://` image URL; a preview appears in the
  form.

The public header and footer link to the dashboard for staff and to the login
page for everyone else. The Django admin stays available at `/admin/` for
accounts, groups and advanced settings, and is linked in the dashboard sidebar
for superusers only.

Creating staff accounts is done in the Django admin
(**Authentication and Authorization → Users**): create the user, tick
*Staff status*, and share the password. Staff do not need *Superuser status*
unless they must delete announcements or manage other accounts.

### Announcement fields

- **Create an announcement**: Dashboard → *New announcement*. Fill at least one
  title and one description (`title_ar`/`title_en`). Leave the other language
  empty to use the automatic fallback.
- **Publish / hide**: the *Publish on the public site* switch, the eye button in
  the list, or the bulk actions. Unpublished announcements never appear publicly.
- **Status**: `open` (still needed), `fulfilled` (goal reached), `closed` (no
  longer relevant). `open` announcements are listed first.
- **Progress**: update *Raised amount*. The percentage is capped at 100 %.
- **Image**: paste an `https://` image URL. A preview appears in the form.
- **Contact**: the contact fields on the announcement override the mosque-wide
  contact details on the detail page. The **contact address** is the address of
  the person responsible for that announcement; leave it empty to show the
  mosque address from `CONTACT_ADDRESS_AR` / `CONTACT_ADDRESS_EN` instead.

### Changing the administrator password

Use the dashboard (**Password** in the sidebar), the Django admin (**user menu →
Change password**), or set `ADMIN_PASSWORD` + `ADMIN_RESET_PASSWORD=True` and
redeploy (then remove the flag), or run on a machine with database access:

```bash
python manage.py changepassword admin@example.org
```

### Other useful commands

```bash
python manage.py ensure_admin                    # create/update the admin
python manage.py ensure_admin --reset-password   # force a password reset
python manage.py seed_demo                       # six bilingual demo entries
python manage.py seed_demo --clear               # delete everything and reseed
python manage.py createsuperuser                 # alternative to ensure_admin
```

---

## 6. Arabic / English translations

Interface strings live in templates and Python and are translated through
gettext.

- Catalog: `locale/ar/LC_MESSAGES/django.po`
- Compiled catalog: `locale/ar/LC_MESSAGES/django.mo` (committed)
- Compiler: `scripts/compile_po.py` (pure Python, no gettext binaries needed)
- Coverage checker: `scripts/check_po.py` (finds strings with no translation)

After editing the `.po` file:

```powershell
.\.venv\Scripts\python.exe scripts\compile_po.py
.\.venv\Scripts\python.exe scripts\check_po.py --list
```

`check_po.py` scans the templates and Python modules, compares them with the
catalog, prints any missing or unused msgid, and exits with code `1` when a
string has no Arabic translation — handy before a deploy or in CI.

The dashboard is fully translated too: every dashboard, form and flash message
string has an Arabic entry, so staff who only read Arabic can work in the same
interface.

Arabic plural forms are handled: `0` → "لا توجد إعلانات", `1` → "إعلان واحد",
`2` → "إعلانان", `3–10` → "… إعلانات", `11+` → "… إعلانًا".

Announcement content is translated by filling the Arabic and English fields in
the admin — no code change needed.

---

## 7. Tests

```powershell
.\.venv\Scripts\python.exe manage.py test
```

The suite covers the model (fallback, progress, validation, location), public
pages (language, RTL/LTR, unpublished filtering, search, filters, detail,
404, health check, Arabic strings), the admin (access control, bulk action) and
the dashboard (anonymous redirect, non-staff `403`, login ar/en,
create/edit/toggle/bulk, superuser-only delete, drafts hidden publicly).

---

## 8. Project structure

```text
config/                     Django project (settings, URLs, WSGI/ASGI)
announcements/
  models.py                 Announcement model, bilingual fallback, progress
  admin.py                  Branded admin with actions and previews
  views.py                  Home, list, detail, about, health check, robots.txt
  context_processors.py     Mosque identity in every template
  templatetags/site_extras.py  Icons, money filter, language switch URL
  management/commands/      ensure_admin, seed_demo
  tests.py                  Public site and admin tests
dashboard/
  views.py                  Overview, list/filters, create/edit, bulk, delete
  forms.py                  Login, password change, announcement form
  decorators.py             staff_required (login redirect or 403)
  tests.py                  Dashboard access and workflow tests
templates/                  Base layout, public pages, partials, admin overrides
templates/dashboard/        Dashboard shell, login, overview, list, form
static/css/app.css          Public design (logical properties → RTL ready)
static/css/dashboard.css    Dashboard + login styling, RTL and responsive
static/css/admin.css        Admin branding
static/js/dashboard.js      Sidebar, select-all, confirmations, image preview
locale/ar/LC_MESSAGES/      Arabic catalog (.po + compiled .mo)
scripts/compile_po.py       PO → MO compiler
scripts/check_po.py         Translation coverage checker
build.sh                    Render build script
render.yaml                 Render Blueprint
docker-compose.yml          Local MySQL 8.4
```

---

## 9. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `DisallowedHost` | Add the domain to `ALLOWED_HOSTS` (comma-separated). |
| `CSRF verification failed` on login | Add `https://your-domain` to `CSRF_TRUSTED_ORIGINS`. |
| `500` at startup: `SECRET_KEY environment variable is required` | Set `SECRET_KEY` (Render does this automatically). |
| `(1045, "Access denied")` | Wrong user/password in `DATABASE_URL`; URL-encode special characters (`@` → `%40`). |
| `(2003, "Can't connect to MySQL server")` | Check the host, port and the provider's firewall. |
| TLS/certificate errors | Provide `DB_SSL_CA`, or set `DB_SSL_VERIFY=False` for providers with self-signed certificates. |
| Static files unstyled on Render | `build.sh` must run `collectstatic`; check the build log. |
| Arabic strings show in English | The `.mo` file is missing: run `python scripts/compile_po.py` and commit it. |
| Dashboard returns `403` after login | The account lacks **Staff status**; tick it in the Django admin. |
| `check_po.py` exits with code 1 | Some interface strings have no Arabic translation; run it with `--list`. |
| Login redirects in a loop over plain HTTP | `DEBUG=False` sets secure cookies; use HTTPS (Render) or `DEBUG=True` locally. |
| Admin password not updated | Set `ADMIN_RESET_PASSWORD=True` for one deploy, then remove it. |
| SQLite data disappears on Render | The free tier has an ephemeral disk. Attach a persistent disk (see `render.yaml`) and set `DB_PATH=/data/db.sqlite3`, or switch to MySQL/Postgres via `DATABASE_URL`. |
| The dashboard looks unstyled or "zoomed out" on a phone | The phone kept an old stylesheet. Static URLs now carry a `?v=<mtime>` stamp and dashboard pages are served with `Cache-Control: no-store`, so a normal reload is enough. Close old tabs once after an update. |
| No confirmation after deleting on a phone | The deleted announcement may already be gone (second tap, Back button, second staff member). Delete, publish and edit are idempotent: they return to the list with a message instead of a `404`. |

---

## 10. Security notes

- Announcements are published only by authenticated staff; the public site is
  read-only and has no payment flow.
- The mosque does not collect donations online: visitors are invited to contact
  the mosque directly, which keeps the site honest and simple.
- For a public deployment: keep `DEBUG=False`, use a strong `SECRET_KEY`,
  change the default password, and consider `SECURE_SSL_REDIRECT=True` and
  `SECURE_HSTS_SECONDS=31536000` once the domain is stable.
