from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from bagel_shop.apps.core.views import media_file

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("health/", include("bagel_shop.apps.core.urls")),
    path("media/<path:name>", media_file, name="media_file"),
    path("admin/", admin.site.urls),
]

urlpatterns += i18n_patterns(
    path("", include("bagel_shop.apps.pages.urls")),
    path("menu/", include("bagel_shop.apps.catalog.urls")),
    path("cart/", include("bagel_shop.apps.cart.urls")),
    path("checkout/", include("bagel_shop.apps.checkout.urls")),
    path("drops/", include("bagel_shop.apps.drops.urls")),
    path("orders/", include("bagel_shop.apps.orders.urls")),
    path("blog/", include("bagel_shop.apps.blog.urls")),
    path("payments/", include("bagel_shop.apps.payments.urls")),
    path("newsletter/", include("bagel_shop.apps.notifications.urls")),
    path("accounts/", include("bagel_shop.apps.accounts.urls")),
)

if settings.DEBUG:
    urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
