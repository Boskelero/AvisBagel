from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

from bagel_shop.apps.cart.services import add_bundle_to_cart

from .forms import BundleBuildForm
from .models import BundleTemplate
from .services import get_active_bundle_templates, build_bundle_snapshot


def template_list(request):
    templates = get_active_bundle_templates()
    return render(request, "bundles/bundle_builder.html", {"bundle_templates": templates})


def build_bundle(request, slug):
    bundle_template = get_object_or_404(
        BundleTemplate.objects.filter(is_active=True).prefetch_related("items__product__images"),
        slug=slug,
    )

    form = BundleBuildForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            quantities = {
                str(item.product_id): request.POST.get(f"product_{item.product_id}", "0")
                for item in bundle_template.items.all()
            }
            try:
                snapshot = build_bundle_snapshot(bundle_template, quantities)
                bundle_quantity = form.cleaned_data["bundle_quantity"]
                add_bundle_to_cart(request, snapshot, bundle_quantity)
                messages.success(request, _("Bundle added to cart."))
                return redirect("cart:detail")
            except ValidationError as exc:
                messages.error(request, exc.message)
        else:
            messages.error(request, _("Please correct the highlighted fields."))

    return render(
        request,
        "bundles/bundle_builder.html",
        {
            "bundle_templates": get_active_bundle_templates(),
            "active_bundle": bundle_template,
            "form": form,
        },
    )
