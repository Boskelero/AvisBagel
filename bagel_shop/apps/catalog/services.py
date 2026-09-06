from django.db.models import Prefetch

from bagel_shop.apps.drops.models import DropProduct

from .models import Category, Product, ProductImage


def get_menu_categories_with_products(drop=None):
    products_qs = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related(Prefetch("images", queryset=ProductImage.objects.order_by("sort_order", "id")))
        .order_by("name")
    )
    if drop:
        products_qs = products_qs.prefetch_related(
            Prefetch(
                "drop_entries",
                queryset=DropProduct.objects.filter(drop=drop, is_available=True),
                to_attr="current_drop_entries",
            )
        )
    return (
        Category.objects.filter(is_active=True, products__is_active=True)
        .prefetch_related(Prefetch("products", queryset=products_qs))
        .distinct()
        .order_by("sort_order", "name")
    )


def get_featured_products(limit=6, drop=None):
    queryset = (
        Product.objects.filter(is_active=True, is_featured=True)
        .select_related("category")
        .prefetch_related("images")
        .order_by("name")
    )
    if drop:
        queryset = queryset.prefetch_related(
            Prefetch(
                "drop_entries",
                queryset=DropProduct.objects.filter(drop=drop, is_available=True),
                to_attr="current_drop_entries",
            )
        )
    return queryset[:limit]
