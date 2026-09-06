from django.db import migrations


DEFAULT_PAGE_CONTENT = {
    "menu": {
        "heading_en": "Our menu",
        "intro_en": "Browse our bagels and seasonal specials. Availability changes with each Drop.",
    },
    "about": {
        "heading_en": "Our bakery story",
        "intro_en": "Abu Avi Bagels started with one oven and a goal: to serve honest bagels with strong local character.",
        "content_en": "<p>We focus on quality flour, long fermentation, and classic baking techniques with fresh ingredients from local suppliers.</p>",
    },
    "contact": {
        "heading_en": "How can we help?",
        "intro_en": "Questions about an order, pickup, ingredients, or anything else? Send us a message.",
    },
    "catering": {
        "heading_en": "Bring better bagels to the table.",
        "intro_en": "From office breakfasts to simchas and private parties, tell Avi what you are planning and we will shape the order around your event.",
    },
    "blog": {
        "heading_en": "Bagel journal",
        "intro_en": "Stories, baking tips, and seasonal updates from our bakery.",
    },
}


def seed_page_content(apps, schema_editor):
    PageMetadata = apps.get_model("core", "PageMetadata")
    for page_key, values in DEFAULT_PAGE_CONTENT.items():
        page, _ = PageMetadata.objects.get_or_create(page_key=page_key)
        changed_fields = []
        for field_name, value in values.items():
            if not getattr(page, field_name):
                setattr(page, field_name, value)
                changed_fields.append(field_name)
        if changed_fields:
            page.save(update_fields=changed_fields)


class Migration(migrations.Migration):
    dependencies = [("core", "0002_pagemetadata_visible_content")]

    operations = [migrations.RunPython(seed_page_content, migrations.RunPython.noop)]
