"""ASGI config for bagel_shop project."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bagel_shop.config.settings")

application = get_asgi_application()
