from django.contrib import admin

from .models import Post, PostCategory


@admin.register(PostCategory)
class PostCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("admin_title", "category", "status", "published_at")
    list_filter = ("status", "category")
    search_fields = (
        "title_en",
        "title_he",
        "excerpt_en",
        "excerpt_he",
        "content_en",
        "content_he",
        "title",
        "excerpt",
        "content",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "category",
                    "status",
                    "published_at",
                    "slug",
                    "cover_image",
                )
            },
        ),
        (
            "English",
            {
                "fields": (
                    "title_en",
                    "excerpt_en",
                    "content_en",
                )
            },
        ),
        (
            "Hebrew",
            {
                "fields": (
                    "title_he",
                    "excerpt_he",
                    "content_he",
                )
            },
        ),
        (
            "Legacy fallback",
            {
                "classes": ("collapse",),
                "fields": (
                    "title",
                    "excerpt",
                    "content",
                ),
            },
        ),
    )

    @admin.display(description="Title")
    def admin_title(self, obj):
        return obj.title_en or obj.title_he or obj.title or obj.slug
