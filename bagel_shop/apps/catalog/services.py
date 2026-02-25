from django.db.models import Prefetch

from .models import Category, Product, ProductImage


def get_menu_categories_with_products():
    products_qs = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related(Prefetch("images", queryset=ProductImage.objects.order_by("sort_order", "id")))
        .order_by("name")
    )
    return (
        Category.objects.filter(is_active=True)
        .prefetch_related(Prefetch("products", queryset=products_qs))
        .order_by("sort_order", "name")
    )


def get_featured_products(limit=6):
    return (
        Product.objects.filter(is_active=True, is_featured=True)
        .select_related("category")
        .prefetch_related("images")
        .order_by("name")[:limit]
    )
