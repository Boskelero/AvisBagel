from django.shortcuts import get_object_or_404, render

from .forms import AddToCartForm
from .models import Product
from .services import get_menu_categories_with_products


def product_list(request):
    categories = get_menu_categories_with_products()
    return render(request, "catalog/product_list.html", {"categories": categories})


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.filter(is_active=True).prefetch_related("images", "category"),
        slug=slug,
    )
    form = AddToCartForm()
    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "add_to_cart_form": form,
        },
    )
