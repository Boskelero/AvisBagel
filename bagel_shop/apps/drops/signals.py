from django.db.models.signals import post_save
from django.dispatch import receiver

from bagel_shop.apps.orders.models import Order

from .models import DropReservation


@receiver(post_save, sender=Order)
def keep_capacity_in_sync_with_order(sender, instance, **kwargs):
    try:
        reservation = instance.capacity_reservation
    except DropReservation.DoesNotExist:
        return

    desired_status = None
    if instance.status == Order.STATUS_CANCELED:
        desired_status = DropReservation.STATUS_RELEASED
    elif instance.status in {
        Order.STATUS_PENDING_PAYMENT,
        Order.STATUS_PAID,
        Order.STATUS_PREPARING,
        Order.STATUS_READY,
        Order.STATUS_COMPLETED,
    }:
        desired_status = DropReservation.STATUS_CONFIRMED
    if desired_status and reservation.status != desired_status:
        reservation.status = desired_status
        reservation.save(update_fields=["status", "updated_at"])
