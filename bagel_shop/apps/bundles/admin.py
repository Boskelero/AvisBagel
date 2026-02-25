from django.contrib import admin

from .models import BundleTemplate, BundleTemplateItem


class BundleTemplateItemInline(admin.TabularInline):
    model = BundleTemplateItem
    extra = 1


@admin.register(BundleTemplate)
class BundleTemplateAdmin(admin.ModelAdmin):
    list_display = ("admin_name", "min_items", "max_items", "is_active")
    list_editable = ("is_active",)
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
                "fields": ("slug", "min_items", "max_items", "is_active"),
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
    inlines = [BundleTemplateItemInline]

    @admin.display(description="Name")
    def admin_name(self, obj):
        return obj.name_en or obj.name_he or obj.name or obj.slug


@admin.register(BundleTemplateItem)
class BundleTemplateItemAdmin(admin.ModelAdmin):
    list_display = ("bundle_template", "product", "max_quantity", "sort_order")
    list_filter = ("bundle_template",)
