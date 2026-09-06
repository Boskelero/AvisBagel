from django.conf import settings

from .models import PageMetadata


PAGE_ROUTE_MAP = {
    ("pages", "home"): PageMetadata.PAGE_HOME,
    ("catalog", "menu"): PageMetadata.PAGE_MENU,
    ("pages", "about"): PageMetadata.PAGE_ABOUT,
    ("pages", "contact"): PageMetadata.PAGE_CONTACT,
    ("pages", "catering"): PageMetadata.PAGE_CATERING,
    ("blog", "post_list"): PageMetadata.PAGE_BLOG,
}


def site_defaults(request):
    match = getattr(request, "resolver_match", None)
    page_key = PAGE_ROUTE_MAP.get((match.namespace, match.url_name)) if match else None
    page_meta = PageMetadata.objects.filter(page_key=page_key).first() if page_key else None
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_PHONE": settings.SITE_PHONE,
        "SITE_EMAIL": settings.SITE_EMAIL,
        "SITE_ADDRESS": settings.SITE_ADDRESS,
        "PAGE_META": page_meta,
    }
