from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import BundleTemplate


def get_active_bundle_templates():
    return BundleTemplate.objects.filter(is_active=True).prefetch_related(
        "items__product__images"
    )


def build_bundle_snapshot(bundle_template, posted_quantities):
    selected_items = []
    total_items = 0
    unit_price_cents = 0

    for option in bundle_template.items.select_related("product").all():
        raw_qty = posted_quantities.get(str(option.product_id), 0)
        try:
            quantity = int(raw_qty)
        except (TypeError, ValueError):
            quantity = 0

        if quantity < 0:
            raise ValidationError(_("Quantity cannot be negative."))
        if quantity > option.max_quantity:
            raise ValidationError(
                _("Selected quantity exceeds bundle limit for %(product)s.")
                % {"product": option.product.name_i18n}
            )

        if quantity == 0:
            continue

        line_total = option.product.price_cents * quantity
        total_items += quantity
        unit_price_cents += line_total
        selected_items.append(
            {
                "product_id": option.product_id,
                "name": option.product.name_i18n,
                "slug": option.product.slug,
                "quantity": quantity,
                "unit_price_cents": option.product.price_cents,
                "line_total_cents": line_total,
            }
        )

    if total_items < bundle_template.min_items or total_items > bundle_template.max_items:
        raise ValidationError(
            _(
                "Please choose between %(min)s and %(max)s items for this bundle."
            )
            % {
                "min": bundle_template.min_items,
                "max": bundle_template.max_items,
            }
        )

    if not selected_items:
        raise ValidationError(_("Please select at least one product."))

    return {
        "bundle_template_id": bundle_template.id,
        "bundle_name": bundle_template.name_i18n,
        "bundle_slug": bundle_template.slug,
        "min_items": bundle_template.min_items,
        "max_items": bundle_template.max_items,
        "total_items": total_items,
        "unit_price_cents": unit_price_cents,
        "selections": selected_items,
    }
