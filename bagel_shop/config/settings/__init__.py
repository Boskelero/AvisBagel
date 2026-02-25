import os

if os.getenv("DJANGO_ENV", "dev").lower() == "prod":
    from .prod import *  # noqa: F403
else:
    from .dev import *  # noqa: F403
