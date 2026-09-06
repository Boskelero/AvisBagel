from django import forms

from bagel_shop.apps.notifications.models import CateringInquiry, ContactInquiry


class ContactInquiryForm(forms.ModelForm):
    class Meta:
        model = ContactInquiry
        fields = ("name", "email", "phone", "topic", "order_number", "message")
        labels = {
            "phone": "Phone number (optional)",
            "order_number": "Order number (if relevant)",
        }
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class", "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            )


class CateringInquiryForm(forms.ModelForm):
    class Meta:
        model = CateringInquiry
        fields = ("name", "email", "phone", "event_date", "estimated_bagels", "message")
        labels = {"estimated_bagels": "Estimated number of bagels"}
        widgets = {
            "event_date": forms.DateInput(attrs={"type": "date"}),
            "message": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
