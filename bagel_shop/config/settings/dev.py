from .base import *  # noqa: F403

DEBUG = True

if DEBUG:
    INSTALLED_APPS += [  # noqa: F405
        "django_browser_reload",
        "django_watchfiles",
    ]
    MIDDLEWARE += [  # noqa: F405
        "django_browser_reload.middleware.BrowserReloadMiddleware",
    ]

STORAGES = {
    **STORAGES,
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
