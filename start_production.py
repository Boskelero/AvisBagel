"""Prepare and start the production web process.

Railway runs this file for every deployment. Keeping the preparation here makes
deployments self-contained without requiring a separate manual release step.
"""

import os
import subprocess
import sys


def manage(*args: str) -> None:
    subprocess.check_call([sys.executable, "manage.py", *args])


manage("migrate", "--noinput")
manage("collectstatic", "--noinput")

if os.environ.get("SEED_DEMO_DATA", "").lower() in {"1", "true", "yes"}:
    manage("seed_demo_data")

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
