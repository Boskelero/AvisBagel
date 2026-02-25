import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import get_language


class PostCategory(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Post categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Post(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
    ]

    category = models.ForeignKey(
        PostCategory,
        on_delete=models.SET_NULL,
        related_name="posts",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    excerpt = models.CharField(max_length=300, blank=True)
    content = models.TextField(blank=True)
    title_he = models.CharField(max_length=200, blank=True)
    title_en = models.CharField(max_length=200, blank=True)
    excerpt_he = models.CharField(max_length=300, blank=True)
    excerpt_en = models.CharField(max_length=300, blank=True)
    content_he = models.TextField(blank=True)
    content_en = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="blog/", blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title_i18n or self.title or self.slug

    def save(self, *args, **kwargs):
        self.title = self.title or self.title_en or self.title_he
        self.excerpt = self.excerpt or self.excerpt_en or self.excerpt_he
        self.content = self.content or self.content_en or self.content_he

        if not self.slug:
            self.slug = self._build_unique_slug()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.slug})

    def clean(self):
        if not any([self.title_en, self.title_he, self.title]):
            raise ValidationError("Please provide at least one title in Hebrew or English.")
        if not any([self.content_en, self.content_he, self.content]):
            raise ValidationError("Please provide at least one content body in Hebrew or English.")

    def _build_unique_slug(self):
        seed = self.title_en or self.title or self.title_he or f"post-{uuid.uuid4().hex[:8]}"
        base_slug = slugify(seed)
        if not base_slug:
            base_slug = f"post-{uuid.uuid4().hex[:8]}"

        candidate = base_slug
        counter = 2
        while Post.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
            candidate = f"{base_slug}-{counter}"
            counter += 1
        return candidate

    def _localized_value(self, field_name):
        active_language = (get_language() or "he").split("-")[0]
        preferred_field = f"{field_name}_{active_language}"
        fallback_field = f"{field_name}_{'en' if active_language == 'he' else 'he'}"

        for attribute in [preferred_field, fallback_field, field_name]:
            value = getattr(self, attribute, "")
            if isinstance(value, str):
                value = value.strip()
            if value:
                return value
        return ""

    @property
    def title_i18n(self):
        return self._localized_value("title")

    @property
    def excerpt_i18n(self):
        return self._localized_value("excerpt")

    @property
    def content_i18n(self):
        return self._localized_value("content")

    @property
    def excerpt_or_content_i18n(self):
        return self.excerpt_i18n or self.content_i18n
