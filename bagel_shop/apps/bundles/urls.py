from django.urls import path

from . import views

app_name = "bundles"

urlpatterns = [
    path("", views.template_list, name="list"),
    path("<slug:slug>/", views.build_bundle, name="build"),
]
