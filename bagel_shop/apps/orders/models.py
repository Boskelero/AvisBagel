import uuid

from django.db import models


class Order(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PENDING_PAYMENT = "pending_payment"
    STATUS_PAID = "paid"
    STATUS_PREPARING = "preparing"
    STATUS_READY = "ready"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELED = "canceled"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PENDING_PAYMENT, "Pending payment"),
        (STATUS_PAID, "Paid"),
        (STATUS_PREPARING, "Preparing"),
        (STATUS_READY, "Ready"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELED, "Canceled"),
    ]

    FULFILLMENT_PICKUP = "pickup"
    FULFILLMENT_DELIVERY = "delivery"
    FULFILLMENT_CHOICES = [
        (FULFILLMENT_PICKUP, "Pickup"),
        (FULFILLMENT_DELIVERY, "Delivery"),
    ]

    PAYMENT_PAY_ON_PICKUP = "pay_on_pickup"
    PAYMENT_CASH = "cash"
    PAYMENT_CHOICES = [
        (PAYMENT_PAY_ON_PICKUP, "Pay on pickup"),
        (PAYMENT_CASH, "Cash"),
    ]

    number = models.CharField(max_length=24, unique=True, db_index=True)
    customer_name = models.CharField(max_length=160)
    email = models.EmailField()
    phone = models.CharField(max_length=40)
    fulfillment_type = models.CharField(max_length=20, choices=FULFILLMENT_CHOICES)
    pickup_time_slot = models.CharField(max_length=80, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING_PAYMENT,
    )
    subtotal_cents = models.PositiveIntegerField(default=0)
    total_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=3, default="ILS")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.number


class OrderItem(models.Model):
    LINE_TYPE_PRODUCT = "product"
    LINE_TYPE_BUNDLE = "bundle"
    LINE_TYPE_CHOICES = [
        (LINE_TYPE_PRODUCT, "Product"),
        (LINE_TYPE_BUNDLE, "Bundle"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    line_type = models.CharField(max_length=20, choices=LINE_TYPE_CHOICES)
    product_id_snapshot = models.IntegerField(null=True, blank=True)
    product_name = models.CharField(max_length=180)
    product_slug = models.SlugField(max_length=200, blank=True)
    unit_price_cents = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    line_total_cents = models.PositiveIntegerField()
    bundle_snapshot = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.order.number} - {self.product_name}"


class OrderAddress(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="address")
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20, blank=True)
    delivery_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.order.number} address"


def generate_order_number():
    return f"AB{uuid.uuid4().hex[:10].upper()}"
