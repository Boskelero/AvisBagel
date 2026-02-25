from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bagel_shop.apps.blog"
    verbose_name = "Blog"
