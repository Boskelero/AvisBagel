from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import NewsletterSubscriber


def subscribe_email(email):
    subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
    if not created and not subscriber.is_active:
        subscriber.is_active = True
        subscriber.save(update_fields=["is_active"])
    return subscriber, created


def send_order_created_email(order):
    subject = f"Order received: {order.number}"
    body = render_to_string("emails/order_created.txt", {"order": order})
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        fail_silently=True,
    )
