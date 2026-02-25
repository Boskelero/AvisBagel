from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.detail, name="detail"),
    path("add/product/<int:product_id>/", views.add_product, name="add_product"),
    path("remove/<str:line_key>/", views.remove_item, name="remove_item"),
    path("update/<str:line_key>/", views.update_quantity, name="update_quantity"),
    path("update-bundle/<str:line_key>/", views.update_quantity, name="update_bundle_quantity"),
]
