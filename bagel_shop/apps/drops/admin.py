from django.contrib import admin

from .models import BagelPriceTier, Drop, DropProduct, DropReservation


class DropProductInline(admin.TabularInline):
    model = DropProduct
    extra = 1
    autocomplete_fields = ("product",)


@admin.register(Drop)
class DropAdmin(admin.ModelAdmin):
    list_display = (
        "name", "status", "opens_at", "closes_at", "bagel_capacity",
        "reserved_count", "remaining_count", "max_bagels_per_order",
    )
    list_filter = ("status", "opens_at", "pickup_starts_at")
    search_fields = ("name", "pickup_location")
    inlines = [DropProductInline]

    @admin.display(description="Reserved / sold")
    def reserved_count(self, obj):
        return obj.reserved_bagels

    @admin.display(description="Remaining")
    def remaining_count(self, obj):
        return obj.remaining_bagels


@admin.register(DropProduct)
class DropProductAdmin(admin.ModelAdmin):
    list_display = ("drop", "product", "is_available", "price_override_cents", "sort_order")
    list_filter = ("drop", "is_available")
    autocomplete_fields = ("drop", "product")


@admin.register(BagelPriceTier)
class BagelPriceTierAdmin(admin.ModelAdmin):
    list_display = ("quantity", "price_cents", "is_active")
    list_editable = ("price_cents", "is_active")


@admin.register(DropReservation)
class DropReservationAdmin(admin.ModelAdmin):
    list_display = ("drop", "order", "bagel_quantity", "status", "expires_at", "created_at")
    list_filter = ("status", "drop")
    search_fields = ("order__number", "order__customer_name", "order__email")
    readonly_fields = ("created_at", "updated_at")
