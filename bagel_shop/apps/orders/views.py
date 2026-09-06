from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .access import can_view_order
from .models import Order


def detail(request, number):
    order = get_object_or_404(Order.objects.prefetch_related("items"), number=number)
    if not can_view_order(request, order):
        raise Http404
    return render(request, "checkout/success.html", {"order": order})
