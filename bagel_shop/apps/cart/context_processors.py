from .services import get_cart_summary


def cart_summary(request):
    summary = get_cart_summary(request)
    return {
        "cart_item_count": summary["item_count"],
    }
