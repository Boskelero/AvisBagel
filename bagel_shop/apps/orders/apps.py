from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bagel_shop.apps.orders"
    verbose_name = "Orders"
