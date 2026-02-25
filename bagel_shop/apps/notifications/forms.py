from django import forms
from django.utils.translation import gettext_lazy as _


class NewsletterSignupForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        error_messages={"required": _("Please enter an email address.")},
    )
