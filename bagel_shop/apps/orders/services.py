from django.db import transaction

from bagel_shop.apps.drops.models import Drop, DropReservation
from bagel_shop.apps.drops.services import validate_and_lock_capacity

from .models import Order, OrderItem, generate_order_number


def create_order_from_cart(checkout_data, cart_summary):
    if not cart_summary["lines"]:
        raise ValueError("Cannot create order from empty cart.")

    if not cart_summary.get("drop") or cart_summary.get("has_unavailable_items"):
        raise ValueError("Your cart contains items that are unavailable in this Drop.")

    with transaction.atomic():
        # Serialize all final submissions for a Drop, including double-click retries.
        Drop.objects.select_for_update().get(pk=cart_summary["drop"].id)
        existing_order = Order.objects.filter(
            checkout_token=cart_summary["checkout_token"]
        ).first()
        if existing_order:
            return existing_order
        drop = validate_and_lock_capacity(
            cart_summary["drop"].id, cart_summary["bagel_quantity"]
        )
        order = Order.objects.create(
            number=generate_order_number(),
            checkout_token=cart_summary["checkout_token"],
            customer_name=checkout_data["customer_name"],
            email=checkout_data["email"],
            phone=checkout_data["phone"],
            fulfillment_type=Order.FULFILLMENT_PICKUP,
            pickup_time_slot="",
            payment_method=checkout_data["payment_method"],
            subtotal_cents=cart_summary["subtotal_cents"],
            total_cents=cart_summary["estimated_total_cents"],
            discount_cents=cart_summary["discount_cents"],
            bagel_quantity=cart_summary["bagel_quantity"],
            drop=drop,
            status=Order.STATUS_PENDING_PAYMENT,
            notes=checkout_data.get("notes", ""),
        )

        for line in cart_summary["lines"]:
            OrderItem.objects.create(
                order=order,
                line_type=line["type"],
                product_id_snapshot=line.get("product_id"),
                product_name=line.get("name", ""),
                product_slug=line.get("slug", ""),
                unit_price_cents=line["unit_price_cents"],
                quantity=line["quantity"],
                line_total_cents=line["line_total_cents"],
                bundle_snapshot=line.get("bundle_snapshot", {}),
            )

        DropReservation.objects.create(
            drop=drop,
            order=order,
            bagel_quantity=cart_summary["bagel_quantity"],
            status=DropReservation.STATUS_CONFIRMED,
        )

        from bagel_shop.apps.payments.services import create_pay_on_pickup_intent
        from bagel_shop.apps.notifications.services import (
            notify_owner_about_drop_capacity,
            send_order_created_email,
        )

        create_pay_on_pickup_intent(order)
        transaction.on_commit(lambda: send_order_created_email(order))
        transaction.on_commit(lambda: notify_owner_about_drop_capacity(drop))

        return order
