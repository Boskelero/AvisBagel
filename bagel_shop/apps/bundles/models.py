import uuid

from django.db import models
from django.utils.text import slugify
from django.utils.translation import get_language

from bagel_shop.apps.catalog.models import Product


def _localized_value(instance, field_name):
    active_language = (get_language() or "he").split("-")[0]
    fallback_language = "en" if active_language == "he" else "he"
    candidates = [f"{field_name}_{active_language}", f"{field_name}_{fallback_language}", field_name]

    for attribute in candidates:
        value = getattr(instance, attribute, "")
        if isinstance(value, str):
            value = value.strip()
        if value:
            return value
    return ""


def _build_unique_slug(instance_pk, seed, max_length):
    base_slug = slugify(seed or "")
    if not base_slug:
        base_slug = f"bundle-{uuid.uuid4().hex[:8]}"
    base_slug = base_slug[:max_length]

    candidate = base_slug
    counter = 2
    while BundleTemplate.objects.exclude(pk=instance_pk).filter(slug=candidate).exists():
        suffix = f"-{counter}"
        trimmed = base_slug[: max_length - len(suffix)]
        candidate = f"{trimmed}{suffix}"
        counter += 1
    return candidate


class BundleTemplate(models.Model):
    name = models.CharField(max_length=140, blank=True)
    name_he = models.CharField(max_length=140, blank=True)
    name_en = models.CharField(max_length=140, blank=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    description = models.TextField(blank=True)
    description_he = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    min_items = models.PositiveIntegerField(default=6)
    max_items = models.PositiveIntegerField(default=6)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name_en or self.name_he or self.name or self.slug

    def save(self, *args, **kwargs):
        self.name = self.name or self.name_en or self.name_he
        self.description = self.description or self.description_en or self.description_he

        if not self.slug:
            self.slug = _build_unique_slug(
                instance_pk=self.pk,
                seed=self.name_en or self.name or self.name_he,
                max_length=160,
            )
        super().save(*args, **kwargs)

    @property
    def name_i18n(self):
        return _localized_value(self, "name")

    @property
    def description_i18n(self):
        return _localized_value(self, "description")


class BundleTemplateItem(models.Model):
    bundle_template = models.ForeignKey(
        BundleTemplate,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="bundle_items")
    max_quantity = models.PositiveIntegerField(default=12)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        unique_together = ("bundle_template", "product")

    def __str__(self):
        return f"{self.bundle_template.name_i18n} - {self.product.name_i18n}"
