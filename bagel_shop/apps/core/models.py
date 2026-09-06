from django.db import models


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
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=320, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "page metadata"
        verbose_name_plural = "page metadata"

    def __str__(self):
        return self.get_page_key_display()
