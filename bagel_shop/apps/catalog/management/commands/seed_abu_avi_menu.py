from django.core.management.base import BaseCommand

from bagel_shop.apps.catalog.models import Category, Product


class Command(BaseCommand):
    help = "Create or update Abu Avi Bagels' current nine-flavor menu."

    def handle(self, *args, **options):
        Product.objects.filter(
            slug__in=[
                "bagel-sesame", "bagel-poppy", "zaatar-olive-bagel",
                "everything-spiced-bagel", "cream-cheese-herbed",
                "roasted-pepper-labneh",
            ]
        ).update(is_active=False, is_featured=False)
        category, _ = Category.objects.update_or_create(
            slug="bagels",
            defaults={
                "name": "Bagels",
                "name_en": "Bagels",
                "name_he": "בייגלים",
                "description": "Hand-rolled, cold-proofed bagels.",
                "description_en": "Hand-rolled, cold-proofed bagels.",
                "description_he": "בייגלים בעבודת יד ובהתפחה קרה.",
                "is_active": True,
                "sort_order": 1,
            },
        )
        flavors = [
            ("plain", "Plain", 0),
            ("sesame", "Sesame", 0),
            ("poppy", "Poppy", 0),
            ("onion", "Onion", 0),
            ("everything", "Everything", 0),
            ("mediterranean", "Mediterranean", 0),
            ("zaatar", "Zaatar", 0),
            ("cinnamon-raisin", "Cinnamon Raisin", 200),
            ("jalapeno-cheddar", "Jalapeño Cheddar", 300),
        ]
        for sort_order, (slug, name, upcharge) in enumerate(flavors, start=1):
            Product.objects.update_or_create(
                slug=slug,
                defaults={
                    "category": category,
                    "name": name,
                    "name_en": name,
                    "description": "Hand-rolled and cold-proofed in the New York/Jewish tradition.",
                    "description_en": "Hand-rolled and cold-proofed in the New York/Jewish tradition.",
                    "price_cents": 1200 + upcharge,
                    "specialty_upcharge_cents": upcharge,
                    "product_type": Product.TYPE_BAGEL,
                    "is_active": True,
                    "is_featured": sort_order <= 6,
                    "inventory_mode": Product.INVENTORY_MODE_PREORDER,
                },
            )
        self.stdout.write(self.style.SUCCESS("The nine-flavor Abu Avi menu is ready."))
