from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("subscribe/", views.newsletter_subscribe, name="subscribe"),
    path("success/", views.newsletter_success, name="success"),
]
