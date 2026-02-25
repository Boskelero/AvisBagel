from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from bagel_shop.apps.cart.services import clear_cart, get_cart_summary
from bagel_shop.apps.orders.models import Order

from .forms import CheckoutForm
from .services import place_order


def checkout(request):
    cart_summary = get_cart_summary(request)

    if not cart_summary["lines"]:
        messages.error(request, _("Your cart is empty."))
        return redirect("catalog:menu")

    form = CheckoutForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            try:
                order = place_order(form.cleaned_data, cart_summary)
                clear_cart(request)
                messages.success(request, _("Order created successfully."))
                return redirect("checkout:success", number=order.number)
            except ValueError:
                messages.error(request, _("Could not place order. Please try again."))
        else:
            messages.error(request, _("Please correct the highlighted fields."))

    return render(
        request,
        "checkout/checkout.html",
        {
            "form": form,
            **cart_summary,
        },
    )


def success(request, number):
    order = get_object_or_404(Order.objects.prefetch_related("items"), number=number)
    return render(request, "checkout/success.html", {"order": order})
