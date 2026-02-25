from .models import PaymentIntent


def create_pay_on_pickup_intent(order):
    return PaymentIntent.objects.create(
        order=order,
        provider=PaymentIntent.PROVIDER_CASH,
        status=PaymentIntent.STATUS_PENDING,
        amount_cents=order.total_cents,
        currency=order.currency,
        raw_payload={"method": order.payment_method},
    )


def handle_stripe_webhook(payload, signature):
    return {
        "handled": False,
        "reason": "Stripe webhook handler is not implemented yet.",
        "signature": signature,
        "payload": payload,
    }
