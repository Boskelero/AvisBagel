from django.db import transaction

from .models import Order, OrderAddress, OrderItem, generate_order_number


def create_order_from_cart(checkout_data, cart_summary):
    if not cart_summary["lines"]:
        raise ValueError("Cannot create order from empty cart.")

    with transaction.atomic():
        order = Order.objects.create(
            number=generate_order_number(),
            customer_name=checkout_data["customer_name"],
            email=checkout_data["email"],
            phone=checkout_data["phone"],
            fulfillment_type=checkout_data["fulfillment_type"],
            pickup_time_slot=checkout_data.get("pickup_time_slot", ""),
            payment_method=checkout_data["payment_method"],
            subtotal_cents=cart_summary["subtotal_cents"],
            total_cents=cart_summary["estimated_total_cents"],
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

        if checkout_data["fulfillment_type"] == Order.FULFILLMENT_DELIVERY:
            OrderAddress.objects.create(
                order=order,
                line1=checkout_data["address_line1"],
                line2=checkout_data.get("address_line2", ""),
                city=checkout_data["city"],
                postal_code=checkout_data.get("postal_code", ""),
                delivery_notes=checkout_data.get("delivery_notes", ""),
            )

        from bagel_shop.apps.payments.services import create_pay_on_pickup_intent
        from bagel_shop.apps.notifications.services import send_order_created_email

        create_pay_on_pickup_intent(order)
        send_order_created_email(order)

        return order
