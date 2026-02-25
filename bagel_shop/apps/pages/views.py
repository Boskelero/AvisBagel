from django.shortcuts import render

from bagel_shop.apps.blog.services import get_recent_posts
from bagel_shop.apps.bundles.services import get_active_bundle_templates
from bagel_shop.apps.catalog.services import get_featured_products


def home(request):
    return render(
        request,
        "pages/home.html",
        {
            "featured_products": get_featured_products(),
            "bundle_templates": get_active_bundle_templates()[:2],
            "recent_posts": get_recent_posts(limit=2),
        },
    )


def about(request):
    return render(request, "pages/about.html")


def contact(request):
    return render(request, "pages/contact.html")
