from django.conf import settings
from django.core.mail import send_mail, send_mass_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import (
    DropAlert,
    DropAnnouncement,
    DropEmailCampaign,
    NewsletterSubscriber,
)


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
    if settings.SITE_EMAIL and settings.SITE_EMAIL != order.email:
        send_mail(
            subject=f"New Drop order: {order.number}",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.SITE_EMAIL],
            fail_silently=True,
        )


def send_catering_inquiry_email(inquiry):
    if not settings.SITE_EMAIL:
        return
    send_mail(
        subject=f"New catering inquiry from {inquiry.name}",
        message=(
            f"Name: {inquiry.name}\nEmail: {inquiry.email}\nPhone: {inquiry.phone}\n"
            f"Event date: {inquiry.event_date or 'Not specified'}\n"
            f"Estimated bagels: {inquiry.estimated_bagels or 'Not specified'}\n\n"
            f"{inquiry.message}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.SITE_EMAIL],
        fail_silently=True,
    )


def send_contact_inquiry_email(inquiry):
    if not settings.SITE_EMAIL:
        return
    send_mail(
        subject=f"Website message from {inquiry.name}: {inquiry.get_topic_display()}",
        message=(
            f"Name: {inquiry.name}\nEmail: {inquiry.email}\n"
            f"Phone: {inquiry.phone or 'Not provided'}\n"
            f"Topic: {inquiry.get_topic_display()}\n"
            f"Order number: {inquiry.order_number or 'Not provided'}\n\n"
            f"{inquiry.message}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.SITE_EMAIL],
        fail_silently=True,
    )


def notify_owner_about_drop_capacity(drop):
    remaining = drop.remaining_bagels
    if remaining == 0:
        alert_type = DropAlert.TYPE_SOLD_OUT
        subject = f"{drop.name} is sold out"
    elif remaining <= max(6, round(drop.bagel_capacity * 0.2)):
        alert_type = DropAlert.TYPE_LOW_CAPACITY
        subject = f"{drop.name} is nearly sold out"
    else:
        return None
    alert, created = DropAlert.objects.get_or_create(
        drop=drop,
        alert_type=alert_type,
        defaults={"remaining_bagels": remaining},
    )
    if created and settings.SITE_EMAIL:
        send_mail(
            subject=subject,
            message=(
                f"{drop.name} has {remaining} of {drop.bagel_capacity} bagels remaining.\n"
                f"Pickup: {drop.pickup_starts_at:%Y-%m-%d %H:%M}\n"
                "Open the staff dashboard to review the Drop."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.SITE_EMAIL],
            fail_silently=True,
        )
    return alert


def send_drop_announcement(drop):
    existing = DropAnnouncement.objects.filter(drop=drop).first()
    if existing:
        return existing, False
    recipients = list(
        NewsletterSubscriber.objects.filter(is_active=True).values_list("email", flat=True)
    )
    opens_at = timezone.localtime(drop.opens_at)
    closes_at = timezone.localtime(drop.closes_at)
    pickup_starts_at = timezone.localtime(drop.pickup_starts_at)
    pickup_ends_at = timezone.localtime(drop.pickup_ends_at)
    if drop.current_state == "scheduled":
        subject = f"{drop.name} is coming — Abu Avi Bagels"
        opening_line = f"The next Drop is coming. Ordering opens {opens_at:%Y-%m-%d at %H:%M}."
        action_line = f"See the countdown: {settings.SITE_URL.rstrip('/')}/en/"
    else:
        subject = f"{drop.name} is open — Abu Avi Bagels"
        opening_line = f"Ordering is now open for {drop.name}."
        action_line = f"Order here: {settings.SITE_URL.rstrip('/')}/en/drops/order/"
    message = (
        f"{opening_line}\n\n"
        f"Orders close: {closes_at:%Y-%m-%d %H:%M}\n"
        f"Pickup: {pickup_starts_at:%Y-%m-%d %H:%M}–{pickup_ends_at:%H:%M}\n"
        f"Location: {drop.pickup_location}\n\n"
        f"{action_line}"
    )
    messages = [(subject, message, settings.DEFAULT_FROM_EMAIL, [email]) for email in recipients]
    if messages:
        send_mass_mail(messages, fail_silently=False)
    announcement = DropAnnouncement.objects.create(
        drop=drop, recipient_count=len(recipients)
    )
    return announcement, True


def send_drop_closing_reminder(drop):
    existing = DropEmailCampaign.objects.filter(
        drop=drop, campaign_type=DropEmailCampaign.TYPE_CLOSING_SOON
    ).first()
    if existing:
        return existing, False
    recipients = list(
        NewsletterSubscriber.objects.filter(is_active=True).values_list("email", flat=True)
    )
    closes_at = timezone.localtime(drop.closes_at)
    message = (
        f"Only one hour remains to order from {drop.name}.\n\n"
        f"Ordering closes: {closes_at:%Y-%m-%d at %H:%M}\n"
        f"Order here: {settings.SITE_URL.rstrip('/')}/en/drops/order/"
    )
    emails = [
        (
            f"One hour left to order — {drop.name}",
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )
        for email in recipients
    ]
    if emails:
        send_mass_mail(emails, fail_silently=False)
    campaign = DropEmailCampaign.objects.create(
        drop=drop,
        campaign_type=DropEmailCampaign.TYPE_CLOSING_SOON,
        recipient_count=len(recipients),
    )
    return campaign, True


def send_drop_orders_ready(drop):
    existing = DropEmailCampaign.objects.filter(
        drop=drop, campaign_type=DropEmailCampaign.TYPE_ORDERS_READY
    ).first()
    if existing:
        return existing, False
    orders = (
        drop.orders.exclude(status__in=["draft", "canceled"])
        .only("number", "customer_name", "email")
        .order_by("email", "number")
    )
    customers = {}
    for order in orders:
        key = order.email.strip().lower()
        customer = customers.setdefault(
            key,
            {"email": order.email, "name": order.customer_name, "orders": []},
        )
        customer["orders"].append(order.number)
    pickup_starts_at = timezone.localtime(drop.pickup_starts_at)
    pickup_ends_at = timezone.localtime(drop.pickup_ends_at)
    emails = []
    for customer in customers.values():
        order_numbers = ", ".join(customer["orders"])
        emails.append(
            (
                "Your Abu Avi Bagels order is ready",
                (
                    f"Hi {customer['name']},\n\n"
                    f"Your order ({order_numbers}) is ready for pickup.\n"
                    f"Pickup: {pickup_starts_at:%Y-%m-%d %H:%M}–{pickup_ends_at:%H:%M}\n"
                    f"Location: {drop.pickup_location}\n\n"
                    "See you soon!"
                ),
                settings.DEFAULT_FROM_EMAIL,
                [customer["email"]],
            )
        )
    if emails:
        send_mass_mail(emails, fail_silently=False)
    campaign = DropEmailCampaign.objects.create(
        drop=drop,
        campaign_type=DropEmailCampaign.TYPE_ORDERS_READY,
        recipient_count=len(customers),
    )
    return campaign, True
