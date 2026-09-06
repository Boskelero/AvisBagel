RECENT_ORDERS_SESSION_KEY = "recent_order_numbers"


def remember_order(request, order):
    numbers = list(request.session.get(RECENT_ORDERS_SESSION_KEY, []))
    if order.number in numbers:
        numbers.remove(order.number)
    numbers.insert(0, order.number)
    request.session[RECENT_ORDERS_SESSION_KEY] = numbers[:20]
    request.session.modified = True


def can_view_order(request, order):
    return request.user.is_staff or order.number in request.session.get(
        RECENT_ORDERS_SESSION_KEY, []
    )
