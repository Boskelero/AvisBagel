from django.shortcuts import get_object_or_404, render

from .models import Order


def detail(request, number):
    order = get_object_or_404(Order.objects.prefetch_related("items"), number=number)
    return render(request, "checkout/success.html", {"order": order})
