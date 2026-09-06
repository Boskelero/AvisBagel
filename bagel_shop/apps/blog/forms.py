from django import forms

from bagel_shop.apps.core.uploads import validate_image_upload

from .models import Post
from .sanitizers import sanitize_article_html


class BlogSearchForm(forms.Form):
    q = forms.CharField(required=False)


class StaffPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = (
            "category",
            "title_en",
            "excerpt_en",
            "content_en",
            "title_he",
            "excerpt_he",
            "content_he",
            "cover_image",
            "status",
            "published_at",
        )
        labels = {
            "title_en": "English title",
            "excerpt_en": "English summary",
            "content_en": "English article",
            "title_he": "Hebrew title",
            "excerpt_he": "Hebrew summary",
            "content_he": "Hebrew article",
            "cover_image": "Cover image",
            "published_at": "Publish date and time",
        }
        widgets = {
            "excerpt_en": forms.Textarea(attrs={"rows": 3}),
            "content_en": forms.Textarea(attrs={"rows": 10, "class": "form-control js-rich-editor"}),
            "excerpt_he": forms.Textarea(attrs={"rows": 3}),
            "content_he": forms.Textarea(attrs={"rows": 10, "class": "form-control js-rich-editor", "dir": "rtl", "data-direction": "rtl"}),
            "published_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["published_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        for field in self.fields.values():
            field.widget.attrs.setdefault(
                "class", "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            )

    def clean_cover_image(self):
        image = self.cleaned_data.get("cover_image")
        if image:
            validate_image_upload(image)
        return image

    def clean_content_en(self):
        return sanitize_article_html(self.cleaned_data.get("content_en", ""))

    def clean_content_he(self):
        return sanitize_article_html(self.cleaned_data.get("content_he", ""))
