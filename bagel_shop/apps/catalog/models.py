import uuid

from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import get_language


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


def _build_unique_slug(model_cls, instance_pk, seed, max_length, prefix):
    base_slug = slugify(seed or "")
    if not base_slug:
        base_slug = f"{prefix}-{uuid.uuid4().hex[:8]}"
    base_slug = base_slug[:max_length]

    candidate = base_slug
    counter = 2
    while model_cls.objects.exclude(pk=instance_pk).filter(slug=candidate).exists():
        suffix = f"-{counter}"
        trimmed = base_slug[: max_length - len(suffix)]
        candidate = f"{trimmed}{suffix}"
        counter += 1
    return candidate


class Category(models.Model):
    name = models.CharField(max_length=120, blank=True)
    name_he = models.CharField(max_length=120, blank=True)
    name_en = models.CharField(max_length=120, blank=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    description_he = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name_en or self.name_he or self.name or self.slug

    def save(self, *args, **kwargs):
        self.name = self.name or self.name_en or self.name_he
        self.description = self.description or self.description_en or self.description_he

        if not self.slug:
            self.slug = _build_unique_slug(
                model_cls=Category,
                instance_pk=self.pk,
                seed=self.name_en or self.name or self.name_he,
                max_length=140,
                prefix="category",
            )
        super().save(*args, **kwargs)

    @property
    def name_i18n(self):
        return _localized_value(self, "name")

    @property
    def description_i18n(self):
        return _localized_value(self, "description")


class Product(models.Model):
    INVENTORY_MODE_SIMPLE = "simple"
    INVENTORY_MODE_PREORDER = "preorder"
    INVENTORY_MODES = [
        (INVENTORY_MODE_SIMPLE, "Simple"),
        (INVENTORY_MODE_PREORDER, "Preorder"),
    ]

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(max_length=160, blank=True)
    name_he = models.CharField(max_length=160, blank=True)
    name_en = models.CharField(max_length=160, blank=True)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    description = models.TextField(blank=True)
    description_he = models.TextField(blank=True)
    description_en = models.TextField(blank=True)
    price_cents = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    inventory_mode = models.CharField(
        max_length=20,
        choices=INVENTORY_MODES,
        default=INVENTORY_MODE_SIMPLE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name_en or self.name_he or self.name or self.slug

    def save(self, *args, **kwargs):
        self.name = self.name or self.name_en or self.name_he
        self.description = self.description or self.description_en or self.description_he

        if not self.slug:
            self.slug = _build_unique_slug(
                model_cls=Product,
                instance_pk=self.pk,
                seed=self.name_en or self.name or self.name_he,
                max_length=180,
                prefix="product",
            )
        super().save(*args, **kwargs)

    @property
    def primary_image(self):
        image = self.images.filter(is_primary=True).order_by("sort_order", "id").first()
        return image or self.images.order_by("sort_order", "id").first()

    @property
    def name_i18n(self):
        return _localized_value(self, "name")

    @property
    def description_i18n(self):
        return _localized_value(self, "description")

    def get_absolute_url(self):
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.product.name_i18n} image"
