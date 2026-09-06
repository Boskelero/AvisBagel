from django import forms
from django.utils.translation import gettext_lazy as _

from bagel_shop.apps.orders.models import Order


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(
        max_length=160,
        label=_("Full name"),
        error_messages={"required": _("Please enter your full name.")},
    )
    email = forms.EmailField(
        label=_("Email"),
        error_messages={"required": _("Please enter an email address.")},
    )
    phone = forms.CharField(
        max_length=40,
        label=_("Phone number"),
        error_messages={"required": _("Please enter a phone number.")},
    )
    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_CHOICES,
        initial=Order.PAYMENT_PAY_ON_PICKUP,
        label=_("Payment method"),
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        label=_("Order notes"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault("class", "form-select")
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("class", "form-control")
            else:
                field.widget.attrs.setdefault("class", "form-control")
