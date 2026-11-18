"""Django settings for the Qubaa mosque announcements site."""

import os
from pathlib import Path

import pymysql

pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_noop
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load a local .env file for development. On Render, variables come from the
# dashboard and no .env file is present (load_dotenv is then a no-op).
load_dotenv(BASE_DIR / ".env")


def env(name, default=None):
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
DEBUG = os.environ.get("DEBUG", "True") == "True"

SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-local-development-key-change-me"
    else:
        raise ImproperlyConfigured(
            "SECRET_KEY environment variable is required when DEBUG is False."
        )

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
if RENDER_EXTERNAL_HOSTNAME:
    origin = f"https://{RENDER_EXTERNAL_HOSTNAME}"
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

# Render terminates TLS in front of the application.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "announcements",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "dashboard.middleware.DashboardNoStoreMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "django.template.context_processors.static",
                "announcements.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# Production: set DATABASE_URL (mysql://user:password@host:3306/database).
# Local development: without DATABASE_URL, SQLite is used automatically.
database_url = env("DATABASE_URL")

if database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            database_url,
            conn_max_age=int(env("DB_CONN_MAX_AGE", "60")),
            conn_health_checks=True,
        )
    }

    if DATABASES["default"]["ENGINE"].endswith("mysql"):
        options = DATABASES["default"].setdefault("OPTIONS", {})

        # Some providers append ?ssl-mode=... to the URL. dj-database-url puts
        # it in OPTIONS, where PyMySQL does not understand it, so convert it.
        ssl_mode = options.pop("ssl-mode", None) or options.pop("ssl_mode", None)
        ssl_ca = env("DB_SSL_CA")

        if ssl_ca:
            ssl = {"ca": ssl_ca}
            if not env_bool("DB_SSL_VERIFY", True):
                ssl["check_hostname"] = False
            options["ssl"] = ssl
        elif ssl_mode and ssl_mode not in {"disable", "disabled"}:
            # TLS without certificate verification (e.g. ssl-mode=required).
            options["ssl"] = {"check_hostname": False}
else:
    sqlite_name = env("DB_PATH", str(BASE_DIR / "db.sqlite3"))
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": sqlite_name,
            "OPTIONS": {"timeout": 30},
        }
    }

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "dashboard:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "dashboard:login"

# ---------------------------------------------------------------------------
# Internationalization — Arabic (default) and English
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "ar"
LANGUAGES = [
    ("ar", gettext_noop("Arabic")),
    ("en", gettext_noop("English")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files (served by WhiteNoise on Render)
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage"
    },
}

WHITENOISE_ADD_HEADERS = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Application settings (customizable through environment variables)
# ---------------------------------------------------------------------------
SITE_NAME_AR = env("SITE_NAME_AR", "مسجد قباء")
SITE_NAME_EN = env("SITE_NAME_EN", "Qubaa Mosque")
SITE_TAGLINE_AR = env("SITE_TAGLINE_AR", "نخدم مجتمعنا")
SITE_TAGLINE_EN = env("SITE_TAGLINE_EN", "Serving our community")

CONTACT_EMAIL = env("CONTACT_EMAIL", "")
CONTACT_PHONE = env("CONTACT_PHONE", "")
CONTACT_ADDRESS_AR = env("CONTACT_ADDRESS_AR", "")
CONTACT_ADDRESS_EN = env("CONTACT_ADDRESS_EN", "")

DEFAULT_CURRENCY = env("DEFAULT_CURRENCY", "EUR")

# ---------------------------------------------------------------------------
# Sessions, cookies & security
# ---------------------------------------------------------------------------
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # two weeks
CSRF_COOKIE_SAMESITE = "Lax"
LANGUAGE_COOKIE_SAMESITE = "Lax"

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Enable these once the site is served over HTTPS (Render always does).
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
SECURE_HSTS_SECONDS = int(env("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = False
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Only trust proxy headers from Render's router.
USE_X_FORWARDED_HOST = bool(RENDER_EXTERNAL_HOSTNAME)

# ---------------------------------------------------------------------------
# Logging — everything to stdout/stderr so Render captures it
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": env("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
