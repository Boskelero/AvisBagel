from django import forms
from django.db import transaction
from django.forms import BaseModelFormSet

from bagel_shop.apps.catalog.models import Category, Product, ProductImage
from bagel_shop.apps.core.models import PageMetadata
from bagel_shop.apps.core.uploads import validate_image_upload

from .models import BagelPriceTier, Drop, DropProduct


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name_en", "name_he", "description_en", "description_he", "is_active", "sort_order")
        labels = {
            "name_en": "English name",
            "name_he": "Hebrew name",
            "description_en": "English description",
            "description_he": "Hebrew description",
            "is_active": "Show this category",
            "sort_order": "Display order",
        }
        widgets = {
            "description_en": forms.Textarea(attrs={"rows": 3}),
            "description_he": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-control")


class PageMetadataForm(forms.ModelForm):
    class Meta:
        model = PageMetadata
        fields = ("meta_title", "meta_description")
        labels = {
            "meta_title": "Meta title",
            "meta_description": "Meta description",
        }
        widgets = {"meta_description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["meta_title"].widget.attrs.update({
            "class": "form-control",
            "maxlength": 160,
            "placeholder": "Page title shown in search results and browser tabs",
        })
        self.fields["meta_description"].widget.attrs.update({
            "class": "form-control",
            "maxlength": 320,
            "placeholder": "Short summary shown by search engines and social previews",
        })


class ProductForm(forms.ModelForm):
    price_ils = forms.DecimalField(max_digits=8, decimal_places=2, min_value=0, label="Single price (₪)")
    specialty_upcharge_ils = forms.DecimalField(
        max_digits=8, decimal_places=2, min_value=0, label="Specialty upcharge (₪)", initial=0
    )
    image = forms.ImageField(required=False, help_text="Optional product photo. Uploading a new photo makes it primary.")
    image_alt_text = forms.CharField(required=False, max_length=200, label="Image description")

    class Meta:
        model = Product
        fields = (
            "category", "name_en", "name_he", "description_en", "description_he",
            "product_type", "is_active", "is_featured",
        )
        labels = {
            "name_en": "English name",
            "name_he": "Hebrew name",
            "description_en": "English description",
            "description_he": "Hebrew description",
            "product_type": "Product type",
            "is_active": "Show in the store catalog",
            "is_featured": "Feature this product",
        }
        widgets = {
            "description_en": forms.Textarea(attrs={"rows": 4}),
            "description_he": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["price_ils"].initial = self.instance.price_cents / 100
            self.fields["specialty_upcharge_ils"].initial = self.instance.specialty_upcharge_cents / 100
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            else:
                field.widget.attrs.setdefault(
                    "class", "form-select" if isinstance(field.widget, forms.Select) else "form-control"
                )

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image:
            validate_image_upload(image)
        return image

    @transaction.atomic
    def save(self, commit=True):
        product = super().save(commit=False)
        product.price_cents = int(self.cleaned_data["price_ils"] * 100)
        product.specialty_upcharge_cents = int(self.cleaned_data["specialty_upcharge_ils"] * 100)
        if commit:
            product.save()
            image = self.cleaned_data.get("image")
            if image:
                product.images.update(is_primary=False)
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    alt_text=self.cleaned_data.get("image_alt_text") or product.name_en,
                    is_primary=True,
                )
        return product


class BagelPriceTierForm(forms.ModelForm):
    price_ils = forms.DecimalField(max_digits=8, decimal_places=2, min_value=0, label="Price (₪)")

    class Meta:
        model = BagelPriceTier
        fields = ("quantity", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["price_ils"].initial = self.instance.price_cents / 100
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            else:
                field.widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        tier = super().save(commit=False)
        tier.price_cents = int(self.cleaned_data["price_ils"] * 100)
        if commit:
            tier.save()
        return tier


class BagelPriceTierFormSet(BaseModelFormSet):
    def clean(self):
        super().clean()
        active_quantities = {
            form.cleaned_data.get("quantity")
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE") and form.cleaned_data.get("is_active")
        }
        if 1 not in active_quantities:
            raise forms.ValidationError("An active one-bagel tier is required.")


class DropForm(forms.ModelForm):
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(is_active=True).order_by("product_type", "name"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Only selected products can be ordered in this Drop.",
    )

    class Meta:
        model = Drop
        fields = (
            "name", "status", "opens_at", "closes_at", "pickup_starts_at",
            "pickup_ends_at", "pickup_location", "bagel_capacity",
            "max_bagels_per_order", "products",
        )
        widgets = {
            "opens_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "closes_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "pickup_starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "pickup_ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["opens_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["closes_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["pickup_starts_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["pickup_ends_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        if self.instance.pk:
            self.fields["products"].initial = self.instance.product_entries.filter(
                is_available=True
            ).values_list("product_id", flat=True)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                continue
            field.widget.attrs.setdefault(
                "class", "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            )

    def clean_bagel_capacity(self):
        capacity = self.cleaned_data["bagel_capacity"]
        if self.instance.pk and capacity < self.instance.reserved_bagels:
            raise forms.ValidationError(
                f"Capacity cannot be lower than the {self.instance.reserved_bagels} already reserved bagels."
            )
        return capacity

    def clean(self):
        cleaned_data = super().clean()
        products = cleaned_data.get("products")
        if (
            cleaned_data.get("status") == Drop.STATUS_PUBLISHED
            and products is not None
            and not products.filter(product_type=Product.TYPE_BAGEL).exists()
        ):
            self.add_error("products", "A published Drop must include at least one bagel.")
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            selected_ids = list(self.cleaned_data["products"].values_list("id", flat=True))
            instance.product_entries.exclude(product_id__in=selected_ids).delete()
            for sort_order, product_id in enumerate(selected_ids, start=1):
                DropProduct.objects.update_or_create(
                    drop=instance,
                    product_id=product_id,
                    defaults={"is_available": True, "sort_order": sort_order},
                )
        return instance
