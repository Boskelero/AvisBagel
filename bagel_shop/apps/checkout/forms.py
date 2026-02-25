from django import forms
from django.utils.translation import gettext_lazy as _

from bagel_shop.apps.orders.models import Order


class CheckoutForm(forms.Form):
    PICKUP_SLOTS = [
        ("08:00-10:00", "08:00-10:00"),
        ("10:00-12:00", "10:00-12:00"),
        ("12:00-14:00", "12:00-14:00"),
        ("14:00-16:00", "14:00-16:00"),
        ("16:00-18:00", "16:00-18:00"),
    ]

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
    fulfillment_type = forms.ChoiceField(
        choices=Order.FULFILLMENT_CHOICES,
        initial=Order.FULFILLMENT_PICKUP,
        label=_("Pickup or delivery"),
    )
    pickup_time_slot = forms.ChoiceField(
        choices=PICKUP_SLOTS,
        required=False,
        label=_("Pickup time slot"),
    )
    address_line1 = forms.CharField(max_length=255, required=False, label=_("Street address"))
    address_line2 = forms.CharField(max_length=255, required=False, label=_("Apartment / floor"))
    city = forms.CharField(max_length=120, required=False, label=_("City"))
    postal_code = forms.CharField(max_length=20, required=False, label=_("Postal code"))
    delivery_notes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        label=_("Delivery notes"),
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

    def clean(self):
        cleaned_data = super().clean()
        fulfillment_type = cleaned_data.get("fulfillment_type")

        if fulfillment_type == Order.FULFILLMENT_DELIVERY:
            for field_name, error_message in [
                ("address_line1", _("Please enter your delivery address.")),
                ("city", _("Please enter your city.")),
            ]:
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, error_message)

        if fulfillment_type == Order.FULFILLMENT_PICKUP and not cleaned_data.get("pickup_time_slot"):
            self.add_error("pickup_time_slot", _("Please choose a pickup time slot."))

        return cleaned_data
