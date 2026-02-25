from django.db import models

from bagel_shop.apps.orders.models import Order


class PaymentIntent(models.Model):
    PROVIDER_CASH = "cash"
    PROVIDER_STRIPE = "stripe"
    PROVIDER_CHOICES = [
        (PROVIDER_CASH, "Cash"),
        (PROVIDER_STRIPE, "Stripe"),
    ]

    STATUS_PENDING = "pending"
    STATUS_SUCCEEDED = "succeeded"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCEEDED, "Succeeded"),
        (STATUS_FAILED, "Failed"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payment_intents")
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="ILS")
    provider_intent_id = models.CharField(max_length=180, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.order.number} {self.provider}"
