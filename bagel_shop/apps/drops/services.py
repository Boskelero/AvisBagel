from django.utils import timezone

from .models import BagelPriceTier, Drop, DropReservation


class DropUnavailableError(ValueError):
    pass


class CapacityError(ValueError):
    pass


def get_current_drop(for_update=False):
    now = timezone.now()
    queryset = Drop.objects.filter(
        status=Drop.STATUS_PUBLISHED,
        opens_at__lte=now,
        closes_at__gt=now,
    ).order_by("closes_at")
    if for_update:
        queryset = queryset.select_for_update()
    return queryset.first()


def get_featured_drop():
    now = timezone.now()
    return (
        Drop.objects.filter(status=Drop.STATUS_PUBLISHED, closes_at__gt=now)
        .order_by("opens_at")
        .first()
    )


def calculate_bagel_base_price(quantity):
    if quantity <= 0:
        return 0
    tiers = list(
        BagelPriceTier.objects.filter(is_active=True, quantity__lte=quantity)
        .values_list("quantity", "price_cents")
        .order_by("quantity")
    )
    if not tiers or not any(size == 1 for size, _ in tiers):
        raise ValueError("An active one-bagel price tier is required.")

    best = [0] + [None] * quantity
    for total_quantity in range(1, quantity + 1):
        candidates = [
            best[total_quantity - size] + price
            for size, price in tiers
            if size <= total_quantity and best[total_quantity - size] is not None
        ]
        best[total_quantity] = min(candidates) if candidates else None
    return best[quantity]


def release_expired_reservations(drop):
    return drop.reservations.filter(
        status=DropReservation.STATUS_HELD,
        expires_at__isnull=False,
        expires_at__lte=timezone.now(),
    ).update(status=DropReservation.STATUS_RELEASED)


def validate_and_lock_capacity(drop_id, bagel_quantity):
    drop = Drop.objects.select_for_update().get(pk=drop_id)
    release_expired_reservations(drop)
    if not drop.is_ordering_open:
        raise DropUnavailableError("This Drop is no longer accepting orders.")
    if bagel_quantity <= 0:
        raise CapacityError("An order must contain at least one bagel.")
    if bagel_quantity > drop.max_bagels_per_order:
        raise CapacityError(
            f"This Drop allows a maximum of {drop.max_bagels_per_order} bagels per order."
        )
    if bagel_quantity > drop.remaining_bagels:
        raise CapacityError(f"Only {drop.remaining_bagels} bagels remain in this Drop.")
    return drop
