from django.shortcuts import get_object_or_404, render

from .forms import AddToCartForm
from .models import Product
from .services import get_menu_categories_with_products
from bagel_shop.apps.drops.services import get_current_drop, get_featured_drop


def product_list(request):
    featured_drop = get_featured_drop()
    active_drop = featured_drop if featured_drop and featured_drop.is_ordering_open else None
    categories = get_menu_categories_with_products(featured_drop)
    return render(request, "catalog/product_list.html", {
        "categories": categories,
        "featured_drop": featured_drop,
        "active_drop": active_drop,
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.filter(is_active=True).prefetch_related("images", "category"),
        slug=slug,
    )
    active_drop = get_current_drop()
    featured_drop = get_featured_drop()
    is_available = bool(
        active_drop
        and active_drop.product_entries.filter(product=product, is_available=True).exists()
    )
    is_in_featured_drop = bool(
        featured_drop
        and featured_drop.product_entries.filter(product=product, is_available=True).exists()
    )
    form = AddToCartForm()
    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "add_to_cart_form": form,
            "active_drop": active_drop,
            "featured_drop": featured_drop,
            "is_available": is_available,
            "is_in_featured_drop": is_in_featured_drop,
        },
    )
