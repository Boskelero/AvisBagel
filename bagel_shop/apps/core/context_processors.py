from django.conf import settings


def site_defaults(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_PHONE": settings.SITE_PHONE,
        "SITE_EMAIL": settings.SITE_EMAIL,
        "SITE_ADDRESS": settings.SITE_ADDRESS,
    }
