import uuid

from django.conf import settings


SESSION_CART_KEY = getattr(settings, "CART_SESSION_ID", "cart")


def get_cart_data(request):
    cart = request.session.get(SESSION_CART_KEY)
    if not cart:
        cart = {"lines": []}
        request.session[SESSION_CART_KEY] = cart
    cart.setdefault("lines", [])
    return cart


def save_cart_data(request, cart):
    request.session[SESSION_CART_KEY] = cart
    request.session.modified = True


def add_product_to_cart(request, product, quantity=1):
    cart = get_cart_data(request)
    lines = cart["lines"]
    quantity = max(1, int(quantity))

    existing = next(
        (line for line in lines if line["type"] == "product" and line["product_id"] == product.id),
        None,
    )
    if existing:
        existing["quantity"] += quantity
        existing["unit_price_cents"] = product.price_cents
        existing["name"] = product.name_i18n
        existing["slug"] = product.slug
    else:
        lines.append(
            {
                "key": f"p-{product.id}",
                "type": "product",
                "product_id": product.id,
                "name": product.name_i18n,
                "slug": product.slug,
                "unit_price_cents": product.price_cents,
                "quantity": quantity,
            }
        )

    save_cart_data(request, cart)


def add_bundle_to_cart(request, bundle_snapshot, quantity=1):
    cart = get_cart_data(request)
    lines = cart["lines"]
    quantity = max(1, int(quantity))

    lines.append(
        {
            "key": f"b-{uuid.uuid4().hex[:10]}",
            "type": "bundle",
            "name": bundle_snapshot["bundle_name"],
            "slug": bundle_snapshot.get("bundle_slug", ""),
            "unit_price_cents": bundle_snapshot["unit_price_cents"],
            "quantity": quantity,
            "bundle_snapshot": bundle_snapshot,
        }
    )

    save_cart_data(request, cart)


def remove_line(request, line_key):
    cart = get_cart_data(request)
    cart["lines"] = [line for line in cart["lines"] if line["key"] != line_key]
    save_cart_data(request, cart)


def update_line_quantity(request, line_key, quantity):
    cart = get_cart_data(request)
    quantity = int(quantity)
    for line in cart["lines"]:
        if line["key"] == line_key:
            if quantity <= 0:
                remove_line(request, line_key)
                return
            line["quantity"] = quantity
            break
    save_cart_data(request, cart)


def clear_cart(request):
    request.session[SESSION_CART_KEY] = {"lines": []}
    request.session.modified = True


def get_cart_summary(request):
    cart = get_cart_data(request)
    lines = []
    subtotal_cents = 0

    for line in cart["lines"]:
        line_total = line["unit_price_cents"] * line["quantity"]
        subtotal_cents += line_total
        lines.append(
            {
                **line,
                "line_total_cents": line_total,
            }
        )

    item_count = sum(line["quantity"] for line in lines)
    estimated_total_cents = subtotal_cents

    return {
        "lines": lines,
        "item_count": item_count,
        "subtotal_cents": subtotal_cents,
        "estimated_total_cents": estimated_total_cents,
    }
