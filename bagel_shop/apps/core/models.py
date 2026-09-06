from django.db import models
from django.utils.translation import get_language


class PageMetadata(models.Model):
    PAGE_HOME = "home"
    PAGE_MENU = "menu"
    PAGE_ABOUT = "about"
    PAGE_CONTACT = "contact"
    PAGE_CATERING = "catering"
    PAGE_BLOG = "blog"
    PAGE_CHOICES = [
        (PAGE_HOME, "Home page"),
        (PAGE_MENU, "Menu page"),
        (PAGE_ABOUT, "About page"),
        (PAGE_CONTACT, "Contact page"),
        (PAGE_CATERING, "Catering page"),
        (PAGE_BLOG, "Blog page"),
    ]

    page_key = models.CharField(max_length=30, choices=PAGE_CHOICES, unique=True)
    heading_en = models.CharField(max_length=200, blank=True)
    heading_he = models.CharField(max_length=200, blank=True)
    intro_en = models.TextField(blank=True)
    intro_he = models.TextField(blank=True)
    content_en = models.TextField(blank=True)
    content_he = models.TextField(blank=True)
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=320, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "page metadata"
        verbose_name_plural = "page metadata"

    def __str__(self):
        return self.get_page_key_display()

    def _localized_value(self, field_name):
        active_language = (get_language() or "en").split("-")[0]
        primary = getattr(self, f"{field_name}_{'he' if active_language == 'he' else 'en'}")
        fallback = getattr(self, f"{field_name}_{'en' if active_language == 'he' else 'he'}")
        return primary or fallback

    @property
    def heading_i18n(self):
        return self._localized_value("heading")

    @property
    def intro_i18n(self):
        return self._localized_value("intro")

    @property
    def content_i18n(self):
        return self._localized_value("content")
