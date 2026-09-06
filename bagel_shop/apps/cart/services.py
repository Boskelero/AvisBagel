import uuid

from django.conf import settings

from bagel_shop.apps.catalog.models import Product
from bagel_shop.apps.drops.models import Drop, DropProduct
from bagel_shop.apps.drops.services import calculate_bagel_base_price, get_current_drop


SESSION_CART_KEY = getattr(settings, "CART_SESSION_ID", "cart")


def get_cart_data(request):
    cart = request.session.get(SESSION_CART_KEY)
    if not cart:
        cart = {"lines": []}
        request.session[SESSION_CART_KEY] = cart
    cart.setdefault("lines", [])
    cart.setdefault("drop_id", None)
    cart.setdefault("checkout_token", uuid.uuid4().hex)
    return cart


def save_cart_data(request, cart):
    request.session[SESSION_CART_KEY] = cart
    request.session.modified = True


def add_product_to_cart(request, product, quantity=1):
    active_drop = get_current_drop()
    if not active_drop or not active_drop.is_ordering_open:
        raise ValueError("There is no active Drop accepting orders.")
    listing = DropProduct.objects.filter(
        drop=active_drop, product=product, is_available=True
    ).first()
    if not listing:
        raise ValueError("This product is not available in the current Drop.")

    cart = get_cart_data(request)
    if cart.get("drop_id") != active_drop.id:
        cart = {"drop_id": active_drop.id, "lines": [], "checkout_token": uuid.uuid4().hex}
    lines = cart["lines"]
    quantity = max(1, int(quantity))

    existing = next(
        (line for line in lines if line["type"] == "product" and line["product_id"] == product.id),
        None,
    )
    if existing:
        existing["quantity"] += quantity
        existing["unit_price_cents"] = listing.price_override_cents or product.price_cents
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
                "unit_price_cents": listing.price_override_cents or product.price_cents,
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
    request.session[SESSION_CART_KEY] = {
        "drop_id": None,
        "lines": [],
        "checkout_token": uuid.uuid4().hex,
    }
    request.session.modified = True


def get_cart_summary(request):
    cart = get_cart_data(request)
    drop = Drop.objects.filter(pk=cart.get("drop_id")).first()
    lines = []
    subtotal_cents = 0
    extra_total_cents = 0
    bagel_quantity = 0
    bagel_upcharges_cents = 0
    has_unavailable_items = False
    drop_is_open = bool(drop and drop.is_ordering_open)

    product_ids = [line.get("product_id") for line in cart["lines"] if line.get("type") == "product"]
    products = Product.objects.in_bulk(product_ids)
    listings = {}
    if drop:
        listings = {
            entry.product_id: entry
            for entry in DropProduct.objects.filter(
                drop=drop, product_id__in=product_ids, is_available=True
            )
        }

    for line in cart["lines"]:
        product = products.get(line.get("product_id"))
        listing = listings.get(line.get("product_id"))
        if line.get("type") == "product" and (not product or not listing or not product.is_active):
            has_unavailable_items = True
            line_total = line["unit_price_cents"] * line["quantity"]
        elif product and product.counts_toward_bagel_capacity:
            unit_price = listing.price_override_cents or product.price_cents
            line["unit_price_cents"] = unit_price
            line["name"] = product.name_i18n
            line_total = unit_price * line["quantity"]
            bagel_quantity += line["quantity"]
            bagel_upcharges_cents += product.specialty_upcharge_cents * line["quantity"]
        elif product:
            unit_price = listing.price_override_cents or product.price_cents
            line["unit_price_cents"] = unit_price
            line["name"] = product.name_i18n
            line_total = unit_price * line["quantity"]
            extra_total_cents += line_total
        else:
            # Legacy bundle lines are retained for display but cannot be checked out in a Drop.
            has_unavailable_items = True
            line_total = line["unit_price_cents"] * line["quantity"]
        subtotal_cents += line_total
        lines.append(
            {
                **line,
                "line_total_cents": line_total,
            }
        )

    item_count = sum(line["quantity"] for line in lines)
    try:
        bagel_base_total_cents = calculate_bagel_base_price(bagel_quantity)
    except ValueError:
        bagel_base_total_cents = 0
        if bagel_quantity:
            has_unavailable_items = True
    estimated_total_cents = bagel_base_total_cents + bagel_upcharges_cents + extra_total_cents
    discount_cents = max(0, subtotal_cents - estimated_total_cents)
    exceeds_order_cap = bool(drop and bagel_quantity > drop.max_bagels_per_order)
    exceeds_remaining_capacity = bool(drop and bagel_quantity > drop.remaining_bagels)
    has_bagels = bagel_quantity > 0
    can_checkout = bool(
        lines
        and drop_is_open
        and has_bagels
        and not has_unavailable_items
        and not exceeds_order_cap
        and not exceeds_remaining_capacity
    )

    return {
        "lines": lines,
        "item_count": item_count,
        "subtotal_cents": subtotal_cents,
        "estimated_total_cents": estimated_total_cents,
        "discount_cents": discount_cents,
        "bagel_quantity": bagel_quantity,
        "drop": drop,
        "has_unavailable_items": has_unavailable_items,
        "drop_is_open": drop_is_open,
        "has_bagels": has_bagels,
        "exceeds_order_cap": exceeds_order_cap,
        "exceeds_remaining_capacity": exceeds_remaining_capacity,
        "can_checkout": can_checkout,
        "checkout_token": cart["checkout_token"],
    }
