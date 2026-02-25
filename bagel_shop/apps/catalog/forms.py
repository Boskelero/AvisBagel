from django import forms
from django.utils.translation import gettext_lazy as _


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        max_value=24,
        initial=1,
        label=_("Quantity"),
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 24}),
    )
