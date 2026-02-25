from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from bagel_shop.apps.catalog.models import Product

from .services import (
    add_product_to_cart,
    get_cart_summary,
    remove_line,
    update_line_quantity,
)


def _render_htmx_update(request):
    context = get_cart_summary(request)
    html = render_to_string("cart/partials/cart_updates.html", context, request=request)
    return HttpResponse(html)


def detail(request):
    context = get_cart_summary(request)
    return render(request, "cart/cart_detail.html", context)


@require_POST
def add_product(request, product_id):
    product = get_object_or_404(Product.objects.filter(is_active=True), pk=product_id)
    quantity = request.POST.get("quantity", 1)

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        quantity = 1

    add_product_to_cart(request, product, quantity=quantity)
    messages.success(request, _("Product added to cart."))

    if request.headers.get("HX-Request"):
        return _render_htmx_update(request)

    return redirect("cart:detail")


@require_POST
def remove_item(request, line_key):
    remove_line(request, line_key)

    if request.headers.get("HX-Request"):
        return _render_htmx_update(request)

    return redirect("cart:detail")


@require_POST
def update_quantity(request, line_key):
    quantity = request.POST.get("quantity", 1)

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        quantity = 1

    update_line_quantity(request, line_key, quantity)

    if request.headers.get("HX-Request"):
        return _render_htmx_update(request)

    return redirect("cart:detail")
