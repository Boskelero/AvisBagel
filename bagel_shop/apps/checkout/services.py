from bagel_shop.apps.orders.services import create_order_from_cart


def place_order(checkout_data, cart_summary):
    return create_order_from_cart(checkout_data, cart_summary)
