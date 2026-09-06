from django.apps import AppConfig


class DropsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bagel_shop.apps.drops"

    def ready(self):
        from . import signals  # noqa: F401
