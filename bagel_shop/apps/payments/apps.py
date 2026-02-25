from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bagel_shop.apps.payments"
    verbose_name = "Payments"
