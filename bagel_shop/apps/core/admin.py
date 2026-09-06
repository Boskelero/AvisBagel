from django.contrib import admin

from .models import PageMetadata


@admin.register(PageMetadata)
class PageMetadataAdmin(admin.ModelAdmin):
    list_display = ("page_key", "meta_title", "updated_at")
    readonly_fields = ("page_key", "updated_at")
