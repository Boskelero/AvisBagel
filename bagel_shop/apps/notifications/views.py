from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .forms import NewsletterSignupForm
from .services import subscribe_email


@require_POST
def newsletter_subscribe(request):
    form = NewsletterSignupForm(request.POST)
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"

    if form.is_valid():
        _, created = subscribe_email(form.cleaned_data["email"])
        if created:
            messages.success(request, _("Thank you for joining our newsletter."))
        else:
            messages.info(request, _("This email is already subscribed."))
    else:
        messages.error(request, _("Please provide a valid email address."))

    return redirect(next_url)


def newsletter_success(request):
    return render(request, "notifications/newsletter_success.html")
