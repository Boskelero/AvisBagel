from django.contrib import admin

from .models import Order, OrderAddress, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "line_type",
        "product_id_snapshot",
        "product_name",
        "product_slug",
        "unit_price_cents",
        "quantity",
        "line_total_cents",
        "bundle_snapshot",
    )
    can_delete = False


class OrderAddressInline(admin.StackedInline):
    model = OrderAddress
    extra = 0
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "customer_name",
        "fulfillment_type",
        "payment_method",
        "status",
        "total_cents",
        "created_at",
    )
    list_filter = ("status", "fulfillment_type", "payment_method", "created_at")
    search_fields = ("number", "customer_name", "email", "phone")
    readonly_fields = ("number", "subtotal_cents", "total_cents", "created_at", "updated_at")
    inlines = [OrderItemInline, OrderAddressInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "line_type", "product_name", "quantity", "line_total_cents")
    list_filter = ("line_type",)


@admin.register(OrderAddress)
class OrderAddressAdmin(admin.ModelAdmin):
    list_display = ("order", "line1", "city", "postal_code")
