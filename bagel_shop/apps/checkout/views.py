from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from bagel_shop.apps.cart.services import clear_cart, get_cart_summary
from bagel_shop.apps.orders.models import Order
from bagel_shop.apps.orders.access import can_view_order, remember_order

from .forms import CheckoutForm
from .services import place_order


def checkout(request):
    cart_summary = get_cart_summary(request)

    if not cart_summary["lines"]:
        messages.error(request, _("Your cart is empty."))
        return redirect("catalog:menu")

    if request.method == "GET" and not cart_summary["can_checkout"]:
        if cart_summary["has_unavailable_items"]:
            message = _("Remove unavailable items before checkout.")
        elif not cart_summary["drop_is_open"]:
            message = _("This Drop is not accepting orders.")
        elif not cart_summary["has_bagels"]:
            message = _("Add at least one bagel before checkout.")
        elif cart_summary["exceeds_order_cap"]:
            message = _("Reduce the number of bagels to this Drop's order limit.")
        else:
            message = _("Reduce the order to the number of bagels still available.")
        messages.error(request, message)
        return redirect("cart:detail")

    form = CheckoutForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            try:
                order = place_order(form.cleaned_data, cart_summary)
                remember_order(request, order)
                clear_cart(request)
                messages.success(request, _("Order created successfully."))
                return redirect("checkout:success", number=order.number)
            except ValueError as exc:
                messages.error(request, str(exc))
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
    if not can_view_order(request, order):
        raise Http404
    return render(request, "checkout/success.html", {"order": order})
