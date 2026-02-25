from pathlib import Path

import dj_database_url
from decouple import Csv, config
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parents[3]
PROJECT_DIR = BASE_DIR / "bagel_shop"

SECRET_KEY = config("SECRET_KEY", default="unsafe-secret-key-change-me")
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "storages",
    "bagel_shop.apps.core.apps.CoreConfig",
    "bagel_shop.apps.pages.apps.PagesConfig",
    "bagel_shop.apps.blog.apps.BlogConfig",
    "bagel_shop.apps.catalog.apps.CatalogConfig",
    "bagel_shop.apps.bundles.apps.BundlesConfig",
    "bagel_shop.apps.accounts.apps.AccountsConfig",
    "bagel_shop.apps.cart.apps.CartConfig",
    "bagel_shop.apps.checkout.apps.CheckoutConfig",
    "bagel_shop.apps.orders.apps.OrdersConfig",
    "bagel_shop.apps.payments.apps.PaymentsConfig",
    "bagel_shop.apps.notifications.apps.NotificationsConfig",
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
]

ROOT_URLCONF = "bagel_shop.config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [PROJECT_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "bagel_shop.apps.cart.context_processors.cart_summary",
                "bagel_shop.apps.core.context_processors.site_defaults",
            ],
        },
    },
]

WSGI_APPLICATION = "bagel_shop.config.wsgi.application"
ASGI_APPLICATION = "bagel_shop.config.asgi.application"

default_db_url = f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}"
DATABASES = {
    "default": dj_database_url.parse(
        config("DATABASE_URL", default=default_db_url),
        conn_max_age=config("CONN_MAX_AGE", default=60, cast=int),
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "he"
LANGUAGES = (
    ("he", _("Hebrew")),
    ("en", _("English")),
)
LOCALE_PATHS = [PROJECT_DIR / "locale"]

TIME_ZONE = "Asia/Jerusalem"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [PROJECT_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = PROJECT_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="orders@avisbagel.local")

CART_SESSION_ID = "cart"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SITE_NAME = config("SITE_NAME", default="Avis Bagel")
SITE_EMAIL = config("SITE_EMAIL", default="hello@avisbagel.com")
SITE_PHONE = config("SITE_PHONE", default="03-555-4321")
SITE_ADDRESS = config("SITE_ADDRESS", default="??????? 100, ?? ????")
