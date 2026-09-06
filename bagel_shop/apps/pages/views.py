from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render

from bagel_shop.apps.blog.services import get_recent_posts
from bagel_shop.apps.catalog.services import get_featured_products
from bagel_shop.apps.drops.services import get_featured_drop
from bagel_shop.apps.notifications.services import (
    send_catering_inquiry_email,
    send_contact_inquiry_email,
)

from .forms import CateringInquiryForm, ContactInquiryForm


def home(request):
    featured_drop = get_featured_drop()
    active_drop = featured_drop if featured_drop and featured_drop.is_ordering_open else None
    return render(
        request,
        "pages/home.html",
        {
            "featured_products": get_featured_products(drop=active_drop),
            "featured_drop": featured_drop,
            "active_drop": active_drop,
            "recent_posts": get_recent_posts(limit=2),
        },
    )


def about(request):
    return render(request, "pages/about.html")


def contact(request):
    form = ContactInquiryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        inquiry = form.save()
        transaction.on_commit(lambda: send_contact_inquiry_email(inquiry))
        messages.success(request, "Thanks — we received your message and will get back to you.")
        return redirect("pages:contact")
    return render(request, "pages/contact.html", {"form": form})


def catering(request):
    form = CateringInquiryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        inquiry = form.save()
        transaction.on_commit(lambda: send_catering_inquiry_email(inquiry))
        messages.success(request, "Thanks — Avi will get back to you about the order.")
        return redirect("pages:catering")
    return render(request, "pages/catering.html", {"form": form})
