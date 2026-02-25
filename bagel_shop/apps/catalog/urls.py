from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.product_list, name="menu"),
    path("<slug:slug>/", views.product_detail, name="product_detail"),
]
