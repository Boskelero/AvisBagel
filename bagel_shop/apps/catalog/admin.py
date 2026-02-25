from django.contrib import admin

from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("admin_name", "slug", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("name_en", "name_he", "name", "description_en", "description_he", "description")
    fieldsets = (
        (
            None,
            {
                "fields": ("slug", "is_active", "sort_order"),
            },
        ),
        (
            "English",
            {
                "fields": ("name_en", "description_en"),
            },
        ),
        (
            "Hebrew",
            {
                "fields": ("name_he", "description_he"),
            },
        ),
        (
            "Legacy fallback",
            {
                "classes": ("collapse",),
                "fields": ("name", "description"),
            },
        ),
    )

    @admin.display(description="Name")
    def admin_name(self, obj):
        return obj.name_en or obj.name_he or obj.name or obj.slug


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "admin_name",
        "category",
        "price_cents",
        "is_active",
        "is_featured",
        "inventory_mode",
        "created_at",
    )
    list_filter = ("is_active", "is_featured", "inventory_mode", "category")
    list_editable = ("is_active", "is_featured", "inventory_mode")
    search_fields = (
        "name_en",
        "name_he",
        "name",
        "description_en",
        "description_he",
        "description",
        "slug",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "category",
                    "slug",
                    "price_cents",
                    "inventory_mode",
                    "is_active",
                    "is_featured",
                ),
            },
        ),
        (
            "English",
            {
                "fields": ("name_en", "description_en"),
            },
        ),
        (
            "Hebrew",
            {
                "fields": ("name_he", "description_he"),
            },
        ),
        (
            "Legacy fallback",
            {
                "classes": ("collapse",),
                "fields": ("name", "description"),
            },
        ),
    )
    inlines = [ProductImageInline]

    @admin.display(description="Name")
    def admin_name(self, obj):
        return obj.name_en or obj.name_he or obj.name or obj.slug


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary", "sort_order")
    list_filter = ("is_primary",)
