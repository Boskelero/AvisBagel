from django import forms


class BundleBuildForm(forms.Form):
    bundle_quantity = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 20}),
    )
