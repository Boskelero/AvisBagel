from django.core.management.base import BaseCommand

from bagel_shop.apps.blog.models import Post, PostCategory
from bagel_shop.apps.bundles.models import BundleTemplate, BundleTemplateItem
from bagel_shop.apps.catalog.models import Category, Product


class Command(BaseCommand):
    help = "Seed sample categories, products, bundles, and blog posts."

    def handle(self, *args, **options):
        self.stdout.write("Seeding sample data...")

        classics, _ = Category.objects.get_or_create(
            slug="classics",
            defaults={
                "name": "Classic bagels",
                "name_en": "Classic bagels",
                "name_he": "בייגלים קלאסיים",
                "description": "Classic bagels",
                "description_en": "Classic bagels",
                "description_he": "בייגלים קלאסיים בכל יום",
                "sort_order": 1,
            },
        )
        specials, _ = Category.objects.get_or_create(
            slug="specials",
            defaults={
                "name": "Special creations",
                "name_en": "Special creations",
                "name_he": "מיוחדים",
                "description": "Special creations",
                "description_en": "Special creations",
                "description_he": "טעמים מיוחדים ועונתיים",
                "sort_order": 2,
            },
        )
        spreads, _ = Category.objects.get_or_create(
            slug="spreads",
            defaults={
                "name": "Spreads",
                "name_en": "Spreads",
                "name_he": "ממרחים",
                "description": "Fresh house spreads",
                "description_en": "Fresh house spreads",
                "description_he": "ממרחים טריים מהמטבח שלנו",
                "sort_order": 3,
            },
        )

        products = [
            {
                "category": classics,
                "name": "Bagel Sesame",
                "name_en": "Bagel Sesame",
                "name_he": "בייגל שומשום",
                "slug": "bagel-sesame",
                "description": "Classic sesame crust with soft crumb.",
                "description_en": "Classic sesame crust with soft crumb.",
                "description_he": "ציפוי שומשום קלאסי עם פנים רך ולעיס.",
                "price_cents": 1400,
                "is_featured": True,
            },
            {
                "category": classics,
                "name": "Bagel Poppy",
                "name_en": "Bagel Poppy",
                "name_he": "בייגל פרג",
                "slug": "bagel-poppy",
                "description": "Toasted poppy exterior and chewy center.",
                "description_en": "Toasted poppy exterior and chewy center.",
                "description_he": "מעטפת פריכה עם פרג ומרכז לעיס.",
                "price_cents": 1400,
                "is_featured": True,
            },
            {
                "category": specials,
                "name": "Zaatar Olive Bagel",
                "name_en": "Zaatar Olive Bagel",
                "name_he": "בייגל זעתר וזיתים",
                "slug": "zaatar-olive-bagel",
                "description": "Herb aroma with Kalamata olive notes.",
                "description_en": "Herb aroma with Kalamata olive notes.",
                "description_he": "ניחוח עשבים עם זיתי קלמטה.",
                "price_cents": 1800,
                "is_featured": True,
            },
            {
                "category": specials,
                "name": "Everything Spiced Bagel",
                "name_en": "Everything Spiced Bagel",
                "name_he": "בייגל אול דה ווייס",
                "slug": "everything-spiced-bagel",
                "description": "Sesame, garlic, onion, and sea salt crunch.",
                "description_en": "Sesame, garlic, onion, and sea salt crunch.",
                "description_he": "שומשום, שום, בצל ומלח ים במרקם פריך.",
                "price_cents": 1700,
                "is_featured": True,
            },
            {
                "category": spreads,
                "name": "Cream Cheese Herbed",
                "name_en": "Cream Cheese Herbed",
                "name_he": "שמנת גבינה ועשבים",
                "slug": "cream-cheese-herbed",
                "description": "Whipped cream cheese with garden herbs.",
                "description_en": "Whipped cream cheese with garden herbs.",
                "description_he": "שמנת גבינה מוקצפת עם עשבי תיבול.",
                "price_cents": 1200,
                "is_featured": False,
            },
            {
                "category": spreads,
                "name": "Roasted Pepper Labneh",
                "name_en": "Roasted Pepper Labneh",
                "name_he": "לאבנה פלפל קלוי",
                "slug": "roasted-pepper-labneh",
                "description": "Labneh with smoked pepper and lemon zest.",
                "description_en": "Labneh with smoked pepper and lemon zest.",
                "description_he": "לאבנה עם פלפל מעושן וגרידת לימון.",
                "price_cents": 1300,
                "is_featured": False,
            },
        ]

        product_objs = []
        for payload in products:
            product, _ = Product.objects.update_or_create(
                slug=payload["slug"],
                defaults={
                    "category": payload["category"],
                    "name": payload["name"],
                    "name_en": payload["name_en"],
                    "name_he": payload["name_he"],
                    "description": payload["description"],
                    "description_en": payload["description_en"],
                    "description_he": payload["description_he"],
                    "price_cents": payload["price_cents"],
                    "is_featured": payload["is_featured"],
                    "is_active": True,
                },
            )
            product_objs.append(product)

        half_dozen, _ = BundleTemplate.objects.update_or_create(
            slug="half-dozen-box",
            defaults={
                "name": "Half Dozen Box",
                "name_en": "Half Dozen Box",
                "name_he": "מארז חצי תריסר",
                "description": "Choose six bagels in your custom mix.",
                "description_en": "Choose six bagels in your custom mix.",
                "description_he": "בחרו שישה בייגלים בהרכב אישי.",
                "min_items": 6,
                "max_items": 6,
                "is_active": True,
            },
        )
        dozen, _ = BundleTemplate.objects.update_or_create(
            slug="dozen-box",
            defaults={
                "name": "Dozen Box",
                "name_en": "Dozen Box",
                "name_he": "מארז תריסר",
                "description": "Choose twelve bagels for group orders.",
                "description_en": "Choose twelve bagels for group orders.",
                "description_he": "בחרו שנים עשר בייגלים להזמנה קבוצתית.",
                "min_items": 12,
                "max_items": 12,
                "is_active": True,
            },
        )

        for template in [half_dozen, dozen]:
            BundleTemplateItem.objects.filter(bundle_template=template).delete()
            for i, product in enumerate(product_objs[:4], start=1):
                BundleTemplateItem.objects.create(
                    bundle_template=template,
                    product=product,
                    max_quantity=12,
                    sort_order=i,
                )

        journal, _ = PostCategory.objects.get_or_create(name="Journal", slug="journal")
        Post.objects.update_or_create(
            slug="how-we-boil-our-bagels",
            defaults={
                "category": journal,
                "title": "How we boil our bagels for the right texture",
                "title_en": "How we boil our bagels for the right texture",
                "title_he": "איך אנחנו מבשלים את הבייגלים למרקם הנכון",
                "excerpt": "A practical look at hydration, boiling time, and oven balance.",
                "excerpt_en": "A practical look at hydration, boiling time, and oven balance.",
                "excerpt_he": "מבט מעשי על הידרציה, זמן בישול ואיזון התנור.",
                "content": "We balance fermentation, boil timing, and stone baking to create a shiny crust and chewy interior.",
                "content_en": "We balance fermentation, boil timing, and stone baking to create a shiny crust and chewy interior.",
                "content_he": "אנחנו מאזנים בין תסיסה, זמן בישול ואפייה על אבן כדי ליצור מעטפת מבריקה ופנים לעיס ונעים.",
                "status": Post.STATUS_PUBLISHED,
            },
        )
        Post.objects.update_or_create(
            slug="pickup-guide-for-busy-mornings",
            defaults={
                "category": journal,
                "title": "Pickup guide for busy mornings",
                "title_en": "Pickup guide for busy mornings",
                "title_he": "מדריך איסוף לבקרים עמוסים",
                "excerpt": "How to plan your order window and skip the line.",
                "excerpt_en": "How to plan your order window and skip the line.",
                "excerpt_he": "איך לתכנן חלון הזמנה ולדלג על התור.",
                "content": "Pre-ordering and selecting a pickup slot helps us prepare your bagels at peak freshness.",
                "content_en": "Pre-ordering and selecting a pickup slot helps us prepare your bagels at peak freshness.",
                "content_he": "הזמנה מראש ובחירת חלון איסוף עוזרות לנו להכין את הבייגלים בשיא הטריות.",
                "status": Post.STATUS_PUBLISHED,
            },
        )

        self.stdout.write(self.style.SUCCESS("Seed data created or updated successfully."))
