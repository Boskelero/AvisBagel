from django.urls import path

from . import views

app_name = "checkout"

urlpatterns = [
    path("", views.checkout, name="checkout"),
    path("success/<str:number>/", views.success, name="success"),
]
