from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from bagel_shop.apps.catalog.models import Category, Product
from bagel_shop.apps.blog.models import Post, PostCategory
from bagel_shop.apps.drops.models import BagelPriceTier, Drop, DropProduct, DropReservation
from bagel_shop.apps.drops.services import calculate_bagel_base_price
from bagel_shop.apps.notifications.models import (
    CateringInquiry,
    ContactInquiry,
    NewsletterSubscriber,
)
from bagel_shop.apps.orders.models import Order, OrderItem


CUSTOMERS = [
    "Noa Cohen", "Daniel Levy", "Maya Ben David", "Ariel Mizrahi", "Yael Shapiro",
    "Eitan Katz", "Tamar Gold", "Yonatan Azulay", "Shira Rosen", "Lior Barak",
    "Roni Friedman", "David Biton", "Michal Segal", "Omer Dayan", "Neta Peretz",
    "Amit Klein", "Gal Mor", "Tal Weiss", "Dana Shalev", "Ori Avraham",
]
QUANTITIES = [3, 6, 4, 8, 12, 5, 6, 3, 7, 4, 9, 6, 5, 8, 3, 12, 4, 6, 7, 5]
STATUSES = [
    Order.STATUS_PENDING_PAYMENT,
    Order.STATUS_PAID,
    Order.STATUS_PREPARING,
    Order.STATUS_READY,
    Order.STATUS_COMPLETED,
]


class Command(BaseCommand):
    help = "Create an idempotent demo shop with 9 bagels, 20 customers, and 20 orders."

    @transaction.atomic
    def handle(self, *args, **options):
        call_command("seed_abu_avi_menu", verbosity=0)
        for quantity, price_cents in [(1, 1200), (6, 6500), (12, 12000)]:
            BagelPriceTier.objects.update_or_create(
                quantity=quantity,
                defaults={"price_cents": price_cents, "is_active": True},
            )

        cream_cheese_category, _ = Category.objects.update_or_create(
            slug="cream-cheese",
            defaults={
                "name": "Cream Cheese",
                "name_en": "Cream Cheese",
                "description": "Small-batch spreads for future Drops.",
                "description_en": "Small-batch spreads for future Drops.",
                "is_active": True,
                "sort_order": 2,
            },
        )
        jam_category, _ = Category.objects.update_or_create(
            slug="jams",
            defaults={
                "name": "Jams",
                "name_en": "Jams",
                "description": "Seasonal preserves for future Drops.",
                "description_en": "Seasonal preserves for future Drops.",
                "is_active": True,
                "sort_order": 3,
            },
        )
        extras = [
            (cream_cheese_category, "plain-cream-cheese", "Plain Cream Cheese", 1800),
            (cream_cheese_category, "scallion-cream-cheese", "Scallion Cream Cheese", 2200),
            (jam_category, "strawberry-jam", "Strawberry Jam", 2400),
            (jam_category, "seasonal-jam", "Seasonal Jam", 2600),
        ]
        for category, slug, name, price_cents in extras:
            Product.objects.update_or_create(
                slug=slug,
                defaults={
                    "category": category,
                    "name": name,
                    "name_en": name,
                    "description": "A small-batch extra offered in selected Drops.",
                    "description_en": "A small-batch extra offered in selected Drops.",
                    "price_cents": price_cents,
                    "specialty_upcharge_cents": 0,
                    "product_type": Product.TYPE_EXTRA,
                    "is_active": True,
                    "is_featured": False,
                    "inventory_mode": Product.INVENTORY_MODE_PREORDER,
                },
            )

        now = timezone.now()
        drop, _ = Drop.objects.update_or_create(
            name="Demo Bagel Drop",
            defaults={
                "status": Drop.STATUS_PUBLISHED,
                "opens_at": now - timedelta(hours=2),
                "closes_at": now + timedelta(days=6),
                "pickup_starts_at": now + timedelta(days=7),
                "pickup_ends_at": now + timedelta(days=7, hours=2),
                "pickup_location": "Ben Yehuda 69, Tel Aviv",
                "bagel_capacity": 180,
                "max_bagels_per_order": 12,
            },
        )
        products = list(
            Product.objects.filter(
                slug__in=[
                    "plain", "sesame", "poppy", "onion", "everything",
                    "mediterranean", "zaatar", "cinnamon-raisin", "jalapeno-cheddar",
                ]
            ).order_by("id")
        )
        for sort_order, product in enumerate(products, start=1):
            DropProduct.objects.update_or_create(
                drop=drop,
                product=product,
                defaults={"is_available": True, "sort_order": sort_order},
            )

        for index, (name, quantity) in enumerate(zip(CUSTOMERS, QUANTITIES), start=1):
            product = products[(index - 1) % len(products)]
            upcharge = product.specialty_upcharge_cents * quantity
            total_cents = calculate_bagel_base_price(quantity) + upcharge
            email = f"demo.customer{index:02d}@example.com"
            order, _ = Order.objects.update_or_create(
                number=f"DEMO{index:04d}",
                defaults={
                    "customer_name": name,
                    "email": email,
                    "phone": f"050-700-{index:04d}",
                    "fulfillment_type": Order.FULFILLMENT_PICKUP,
                    "pickup_time_slot": "",
                    "payment_method": Order.PAYMENT_PAY_ON_PICKUP,
                    "status": STATUSES[(index - 1) % len(STATUSES)],
                    "subtotal_cents": product.price_cents * quantity,
                    "total_cents": total_cents,
                    "discount_cents": max(0, product.price_cents * quantity - total_cents),
                    "bagel_quantity": quantity,
                    "drop": drop,
                    "notes": "Demo order for the client preview.",
                },
            )
            order.items.all().delete()
            OrderItem.objects.create(
                order=order,
                line_type=OrderItem.LINE_TYPE_PRODUCT,
                product_id_snapshot=product.id,
                product_name=product.name_en or product.name,
                product_slug=product.slug,
                unit_price_cents=product.price_cents,
                quantity=quantity,
                line_total_cents=total_cents,
            )
            DropReservation.objects.update_or_create(
                order=order,
                defaults={
                    "drop": drop,
                    "bagel_quantity": quantity,
                    "status": DropReservation.STATUS_CONFIRMED,
                },
            )
            created_at = now - timedelta(hours=21 - index)
            Order.objects.filter(pk=order.pk).update(created_at=created_at, updated_at=created_at)
            subscriber, _ = NewsletterSubscriber.objects.update_or_create(
                email=email,
                defaults={"is_active": index % 7 != 0},
            )
            NewsletterSubscriber.objects.filter(pk=subscriber.pk).update(
                created_at=now - timedelta(days=index)
            )

        for index in range(1, 6):
            inquiry, _ = ContactInquiry.objects.update_or_create(
                email=f"demo.question{index:02d}@example.com",
                message=f"Demo customer message {index}: Can you confirm the pickup window?",
                defaults={
                    "name": f"Demo Question {index}",
                    "phone": f"052-800-{index:04d}",
                    "topic": ContactInquiry.TOPIC_PICKUP,
                    "status": ContactInquiry.STATUS_NEW if index <= 3 else ContactInquiry.STATUS_REPLIED,
                },
            )
            ContactInquiry.objects.filter(pk=inquiry.pk).update(created_at=now - timedelta(hours=index))

        for index in range(1, 4):
            inquiry, _ = CateringInquiry.objects.update_or_create(
                email=f"demo.catering{index:02d}@example.com",
                message=f"Demo catering request {index} for an office breakfast.",
                defaults={
                    "name": f"Demo Catering {index}",
                    "phone": f"054-900-{index:04d}",
                    "event_date": (now + timedelta(days=14 + index)).date(),
                    "estimated_bagels": 30 + index * 12,
                    "status": CateringInquiry.STATUS_NEW,
                },
            )
            CateringInquiry.objects.filter(pk=inquiry.pk).update(created_at=now - timedelta(days=index))

        journal_category, _ = PostCategory.objects.update_or_create(
            slug="bagel-journal", defaults={"name": "Bagel Journal"}
        )
        demo_posts = [
            (
                "demo-why-cold-proof-bagels",
                "Why We Cold-Proof Our Bagels",
                "A slow overnight rest builds the flavor and texture we want in every batch.",
                "Great bagels take time. After each bagel is rolled by hand, the dough rests in the cold overnight. This slow fermentation develops deeper flavor and gives the crust its signature character.\n\nThe next day, the bagels are boiled and baked fresh for pickup. It is a longer process, but it is central to the New York and Jewish bagel tradition that inspires Abu Avi Bagels.",
            ),
            (
                "demo-building-your-perfect-dozen",
                "Building Your Perfect Dozen",
                "A quick guide to mixing classic flavors with our rotating specialty bagels.",
                "There is no need to choose only one flavor. Every Drop lets you build your own mix from that week's menu. Start with classics such as Plain, Sesame, Everything, and Poppy, then add a specialty flavor for something different.\n\nDeal pricing is applied automatically when your order reaches six or twelve bagels. Specialty upcharges are calculated separately, so the total is always clear before checkout.",
            ),
            (
                "demo-from-apartment-kitchen-to-drop-day",
                "From the Kitchen to Drop Day",
                "A look behind the scenes at how a limited Abu Avi bagel Drop comes together.",
                "Each Drop begins with a production plan: which flavors to offer, how many bagels can be made, and when pickup will happen. Limiting the batch allows every bagel to be shaped, proofed, boiled, and baked with care.\n\nWhen ordering opens, the shared capacity updates with every completed order. Once the batch is full, the Drop closes so production stays manageable and pickup remains smooth.",
            ),
        ]
        for index, (slug, title, excerpt, content) in enumerate(demo_posts, start=1):
            Post.objects.update_or_create(
                slug=slug,
                defaults={
                    "category": journal_category,
                    "title": title,
                    "title_en": title,
                    "excerpt": excerpt,
                    "excerpt_en": excerpt,
                    "content": content,
                    "content_en": content,
                    "status": Post.STATUS_PUBLISHED,
                    "published_at": now - timedelta(days=index),
                },
            )

        self.stdout.write(self.style.SUCCESS(
            "Demo data ready: 9 bagels, Cream Cheese and Jams extras, 1 live Drop, "
            "20 customers, 20 orders, 20 subscribers, 8 inquiries, and 3 blog posts."
        ))
