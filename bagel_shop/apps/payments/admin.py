from django.contrib import admin

from .models import PaymentIntent


@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = ("order", "provider", "status", "amount_cents", "created_at")
    list_filter = ("provider", "status")
    search_fields = ("order__number", "provider_intent_id")
