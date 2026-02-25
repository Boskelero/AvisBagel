from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("methods/", views.payment_methods, name="methods"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
]
