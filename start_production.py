"""Prepare and start the production web process.

Railway runs this file for every deployment. Keeping the preparation here makes
deployments self-contained without requiring a separate manual release step.
"""

import os
import subprocess
import sys


def manage(*args: str) -> None:
    subprocess.check_call([sys.executable, "manage.py", *args])


def configure_preview_superuser() -> None:
    username = os.environ.get("PREVIEW_ADMIN_USERNAME", "").strip()
    password = os.environ.get("PREVIEW_ADMIN_PASSWORD", "")
    if not username or not password:
        return

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bagel_shop.config.settings")
    import django

    django.setup()
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    user, _ = user_model.objects.get_or_create(username=username)
    user.email = os.environ.get("PREVIEW_ADMIN_EMAIL", "").strip()
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    print(f"Preview superuser '{username}' is ready.", flush=True)


manage("migrate", "--noinput")
manage("collectstatic", "--noinput")

if os.environ.get("SEED_DEMO_DATA", "").lower() in {"1", "true", "yes"}:
    manage("seed_demo_data")

configure_preview_superuser()

port = os.environ.get("PORT", "8000")
os.execvp(
    "gunicorn",
    [
        "gunicorn",
        "bagel_shop.config.wsgi:application",
        "--bind",
        f"0.0.0.0:{port}",
        "--log-file",
        "-",
    ],
)
