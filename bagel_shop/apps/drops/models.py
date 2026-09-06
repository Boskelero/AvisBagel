from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from bagel_shop.apps.catalog.models import Product


class Drop(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PUBLISHED, "Published"),
        (STATUS_CLOSED, "Closed"),
    ]

    name = models.CharField(max_length=160)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    opens_at = models.DateTimeField()
    closes_at = models.DateTimeField()
    pickup_starts_at = models.DateTimeField()
    pickup_ends_at = models.DateTimeField()
    pickup_location = models.CharField(max_length=255)
    bagel_capacity = models.PositiveIntegerField(default=72)
    max_bagels_per_order = models.PositiveIntegerField(default=12)
    products = models.ManyToManyField(Product, through="DropProduct", related_name="drops")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["opens_at"]

    def __str__(self):
        return self.name

    def clean(self):
        errors = {}
        if self.closes_at and self.opens_at and self.closes_at <= self.opens_at:
            errors["closes_at"] = "The ordering cutoff must be after opening time."
        if self.pickup_starts_at and self.closes_at and self.pickup_starts_at < self.closes_at:
            errors["pickup_starts_at"] = "Pickup cannot begin before ordering closes."
        if self.pickup_ends_at and self.pickup_starts_at and self.pickup_ends_at <= self.pickup_starts_at:
            errors["pickup_ends_at"] = "Pickup end must be after pickup start."
        if self.max_bagels_per_order > self.bagel_capacity:
            errors["max_bagels_per_order"] = "The order cap cannot exceed Drop capacity."
        if self.pk and self.bagel_capacity < self.reserved_bagels:
            errors["bagel_capacity"] = "Capacity cannot be lower than already reserved bagels."
        if errors:
            raise ValidationError(errors)

    @property
    def reserved_bagels(self):
        return self.reservations.filter(
            status__in=[DropReservation.STATUS_HELD, DropReservation.STATUS_CONFIRMED]
        ).aggregate(total=Sum("bagel_quantity"))["total"] or 0

    @property
    def remaining_bagels(self):
        return max(0, self.bagel_capacity - self.reserved_bagels)

    @property
    def is_sold_out(self):
        return self.remaining_bagels == 0

    @property
    def is_ordering_open(self):
        now = timezone.now()
        return (
            self.status == self.STATUS_PUBLISHED
            and self.opens_at <= now < self.closes_at
            and not self.is_sold_out
        )

    @property
    def current_state(self):
        now = timezone.now()
        if self.status == self.STATUS_DRAFT:
            return "draft"
        if self.status == self.STATUS_CLOSED:
            return "closed"
        if self.is_sold_out:
            return "sold_out"
        if now < self.opens_at:
            return "scheduled"
        if now >= self.closes_at:
            return "cutoff_reached"
        return "live"

    @property
    def current_state_label(self):
        return {
            "draft": "Draft",
            "closed": "Closed",
            "sold_out": "Sold out",
            "scheduled": "Scheduled",
            "cutoff_reached": "Cutoff reached",
            "live": "Live",
        }[self.current_state]


class DropProduct(models.Model):
    drop = models.ForeignKey(Drop, on_delete=models.CASCADE, related_name="product_entries")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="drop_entries")
    is_available = models.BooleanField(default=True)
    price_override_cents = models.PositiveIntegerField(null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["drop", "product"], name="unique_drop_product")
        ]

    def __str__(self):
        return f"{self.drop} — {self.product}"


class BagelPriceTier(models.Model):
    quantity = models.PositiveIntegerField(unique=True)
    price_cents = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["quantity"]

    def __str__(self):
        return f"{self.quantity} bagel(s) — {self.price_cents / 100:.2f} ILS"


class DropReservation(models.Model):
    STATUS_HELD = "held"
    STATUS_CONFIRMED = "confirmed"
    STATUS_RELEASED = "released"
    STATUS_CHOICES = [
        (STATUS_HELD, "Held for payment"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_RELEASED, "Released"),
    ]

    drop = models.ForeignKey(Drop, on_delete=models.PROTECT, related_name="reservations")
    order = models.OneToOneField(
        "orders.Order", on_delete=models.CASCADE, related_name="capacity_reservation"
    )
    bagel_quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_HELD)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.drop} — {self.bagel_quantity} — {self.status}"
