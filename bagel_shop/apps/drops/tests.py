from datetime import timedelta
from io import BytesIO

from django.core.management import call_command
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core import mail
from openpyxl import load_workbook
from PIL import Image

from bagel_shop.apps.catalog.models import Category, Product
from bagel_shop.apps.blog.models import Post
from bagel_shop.apps.orders.models import Order
from bagel_shop.apps.notifications.models import (
    CateringInquiry,
    ContactInquiry,
    DropAlert,
    DropAnnouncement,
    DropEmailCampaign,
    NewsletterSubscriber,
)
from bagel_shop.apps.notifications.services import notify_owner_about_drop_capacity

from .models import BagelPriceTier, Drop, DropProduct, DropReservation
from .services import calculate_bagel_base_price


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class DropOrderingTests(TestCase):
    def setUp(self):
        BagelPriceTier.objects.all().delete()
        BagelPriceTier.objects.bulk_create([
            BagelPriceTier(quantity=1, price_cents=1200),
            BagelPriceTier(quantity=6, price_cents=6500),
            BagelPriceTier(quantity=12, price_cents=12000),
        ])
        category = Category.objects.create(name="Bagels", name_en="Bagels", slug="bagels-test")
        self.plain = Product.objects.create(
            category=category,
            name="Plain",
            name_en="Plain",
            slug="plain-test",
            price_cents=1200,
            product_type=Product.TYPE_BAGEL,
        )
        self.jalapeno = Product.objects.create(
            category=category,
            name="Jalapeño Cheddar",
            name_en="Jalapeño Cheddar",
            slug="jalapeno-test",
            price_cents=1500,
            specialty_upcharge_cents=300,
            product_type=Product.TYPE_BAGEL,
        )
        now = timezone.now()
        self.drop = Drop.objects.create(
            name="Thursday Drop",
            status=Drop.STATUS_PUBLISHED,
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=2),
            pickup_starts_at=now + timedelta(hours=3),
            pickup_ends_at=now + timedelta(hours=5),
            pickup_location="Ben Yehuda 69, Tel Aviv",
            bagel_capacity=72,
            max_bagels_per_order=12,
        )
        DropProduct.objects.create(drop=self.drop, product=self.plain)
        DropProduct.objects.create(drop=self.drop, product=self.jalapeno)

    def _add(self, client, product, quantity):
        return client.post(reverse("cart:add_product", args=[product.id]), {"quantity": quantity})

    def _checkout(self, client):
        return client.post(
            reverse("checkout:checkout"),
            {
                "customer_name": "Test Customer",
                "email": "test@example.com",
                "phone": "0501234567",
                "payment_method": Order.PAYMENT_PAY_ON_PICKUP,
                "notes": "",
            },
        )

    def test_tiered_pricing_uses_best_combination(self):
        self.assertEqual(calculate_bagel_base_price(5), 6000)
        self.assertEqual(calculate_bagel_base_price(6), 6500)
        self.assertEqual(calculate_bagel_base_price(8), 8900)
        self.assertEqual(calculate_bagel_base_price(12), 12000)
        self.assertEqual(calculate_bagel_base_price(18), 18500)

    def test_order_builder_stays_image_free_and_links_to_product_details(self):
        self.plain.description_en = (
            "Hand-rolled and cold-proofed in the New York and Jewish tradition."
        )
        self.jalapeno.description_en = (
            "Cheddar dough with jalapeño for a savory and gently spicy finish."
        )
        self.plain.save(update_fields=["description_en"])
        self.jalapeno.save(update_fields=["description_en"])
        response = Client().get(reverse("drops:order"))
        self.assertContains(
            response,
            reverse("catalog:product_detail", args=[self.plain.slug]),
        )
        self.assertContains(response, "View details", count=2)
        self.assertNotContains(response, "order-product-image")
        self.assertContains(response, "Hand-rolled and cold-proofed in the New York…")
        self.assertContains(response, "Cheddar dough with jalapeño for a savory and…")
        self.assertNotContains(response, "Classic bagel · eligible for bundle savings")
        self.assertContains(response, "Includes ₪3.00 specialty add-on")

    def test_cart_and_checkout_explain_deal_pricing_and_pickup(self):
        client = Client()
        self._add(client, self.plain, 6)

        cart = client.get(reverse("cart:detail"))
        self.assertContains(cart, "Automatic deal pricing")
        self.assertContains(cart, "Six bagels cost ₪65")
        self.assertContains(cart, "Pickup")
        self.assertContains(cart, "Bagel deal savings")

        checkout = client.get(reverse("checkout:checkout"))
        self.assertContains(checkout, "How pickup works")
        self.assertContains(checkout, "How was my discount calculated?")
        self.assertContains(checkout, "Pickup only")

    def test_empty_cart_uses_friendly_full_width_state(self):
        response = Client().get(reverse("cart:detail"))
        self.assertContains(response, "Your cart is empty")
        self.assertContains(response, 'class="col-12"', html=False)
        self.assertNotContains(response, "Order summary")

    def test_six_pack_adds_only_specialty_upcharge(self):
        client = Client()
        self._add(client, self.plain, 5)
        self._add(client, self.jalapeno, 1)
        response = self._checkout(client)
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.bagel_quantity, 6)
        self.assertEqual(order.total_cents, 6800)
        self.assertEqual(order.discount_cents, 700)
        self.assertEqual(order.capacity_reservation.status, DropReservation.STATUS_CONFIRMED)

    def test_order_confirmation_is_private_to_customer_session(self):
        client = Client()
        self._add(client, self.plain, 1)
        self._checkout(client)
        order = Order.objects.get()
        url = reverse("checkout:success", args=[order.number])
        self.assertEqual(client.get(url).status_code, 200)
        self.assertEqual(Client().get(url).status_code, 404)

    def test_order_cap_is_enforced_at_checkout(self):
        client = Client()
        self._add(client, self.plain, 13)
        response = self._checkout(client)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "maximum of 12 bagels")
        self.assertFalse(Order.objects.exists())

    def test_shared_capacity_cannot_be_oversold(self):
        self.drop.bagel_capacity = 6
        self.drop.max_bagels_per_order = 6
        self.drop.save()
        first = Client()
        second = Client()
        self._add(first, self.plain, 6)
        self._add(second, self.plain, 1)
        self.assertEqual(self._checkout(first).status_code, 302)

        response = self._checkout(second)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no longer accepting orders")
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(self.drop.remaining_bagels, 0)
        home = Client().get(reverse("pages:home"))
        self.assertContains(home, "This Drop sold out")
        self.assertNotContains(home, "Ordering opens in")

    def test_canceling_order_releases_capacity(self):
        client = Client()
        self._add(client, self.plain, 6)
        self._checkout(client)
        order = Order.objects.get()
        order.status = Order.STATUS_CANCELED
        order.save()
        order.capacity_reservation.refresh_from_db()
        self.assertEqual(order.capacity_reservation.status, DropReservation.STATUS_RELEASED)
        self.assertEqual(self.drop.remaining_bagels, 72)

    def test_product_outside_drop_cannot_be_added(self):
        extra = Product.objects.create(
            category=self.plain.category,
            name="Future flavor",
            slug="future-test",
            price_cents=1200,
        )
        response = self._add(Client(), extra, 1)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Order.objects.exists())

    def test_products_outside_the_drop_are_presented_as_rotating_menu_items(self):
        future = Product.objects.create(
            category=self.plain.category,
            name="Future flavor",
            name_en="Future flavor",
            slug="future-menu-test",
            price_cents=1200,
        )
        menu = Client().get(reverse("catalog:menu"))
        self.assertContains(menu, "Available in selected Drops")
        self.assertNotContains(menu, ">Unavailable<")

        detail = Client().get(reverse("catalog:product_detail", args=[future.slug]))
        self.assertContains(detail, "Part of our rotating menu")
        self.assertContains(detail, "Get Drop alerts")
        self.assertNotContains(detail, "not available in the current Drop")

    def test_drop_home_and_menu_render(self):
        response = Client().get(reverse("pages:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thursday Drop")
        self.assertContains(response, "The Drop is live")
        self.assertNotContains(response, "bagel-header-1.jpg")
        response = Client().get(reverse("catalog:menu"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ordering is open")

    def test_mobile_order_builder_creates_drop_cart(self):
        client = Client()
        page = client.get(reverse("drops:order"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "72 bagels")
        self.assertContains(page, "How deal pricing works")
        self.assertContains(page, "Save ₪7.00")
        self.assertContains(page, "₪15.00")
        response = client.post(
            reverse("drops:order"),
            {
                f"product_{self.plain.id}": 5,
                f"product_{self.jalapeno.id}": 1,
            },
        )
        self.assertRedirects(response, reverse("cart:detail"))
        cart = client.session["cart"]
        self.assertEqual(cart["drop_id"], self.drop.id)
        self.assertEqual(sum(line["quantity"] for line in cart["lines"]), 6)

    def test_order_builder_preserves_quantities_after_validation_error(self):
        response = Client().post(
            reverse("drops:order"),
            {
                f"product_{self.plain.id}": 12,
                f"product_{self.jalapeno.id}": 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="12" data-bagel-quantity')
        self.assertContains(response, 'value="1" data-bagel-quantity')
        self.assertContains(response, "up to 12 bagels per order")

    def test_staff_dashboard_and_core_pages_require_staff(self):
        anonymous = Client()
        response = anonymous.get(reverse("drops:staff_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("drops:staff_login"), response.url)

        staff = get_user_model().objects.create_user(
            username="avi", password="test-password", is_staff=True
        )
        client = Client()
        client.force_login(staff)
        self.assertEqual(client.get(reverse("drops:staff_dashboard")).status_code, 200)
        self.assertEqual(client.get(reverse("drops:staff_orders")).status_code, 200)
        self.assertEqual(client.get(reverse("drops:staff_customers")).status_code, 200)
        self.assertEqual(client.get(reverse("drops:staff_products")).status_code, 200)
        self.assertEqual(client.get(reverse("drops:staff_blog_posts")).status_code, 200)
        self.assertEqual(client.get(reverse("drops:staff_categories")).status_code, 200)
        self.assertEqual(client.get(reverse("drops:staff_pricing")).status_code, 200)
        self.assertEqual(client.get(reverse("drops:staff_seo")).status_code, 200)
        self.assertEqual(client.get(reverse("drops:staff_inquiries")).status_code, 200)
        self.assertEqual(client.get(reverse("drops:staff_subscribers")).status_code, 200)
        for export_name in [
            "staff_orders_excel",
            "staff_customers_excel",
            "staff_products_excel",
            "staff_inquiries_excel",
            "staff_subscribers_excel",
        ]:
            export = client.get(reverse(f"drops:{export_name}"))
            self.assertEqual(export.status_code, 200)
            self.assertTrue(export.content.startswith(b"PK"))
        self.assertEqual(client.get(reverse("drops:staff_edit", args=[self.drop.id])).status_code, 200)
        self.assertEqual(client.get(reverse("drops:staff_production_sheet", args=[self.drop.id])).status_code, 200)
        self.assertTrue(
            client.get(reverse("drops:staff_excel", args=[self.drop.id])).content.startswith(b"PK")
        )
        dashboard = client.get(reverse("drops:staff_dashboard"))
        self.assertContains(dashboard, "Total order value")
        self.assertContains(dashboard, "Previous Drops")
        self.assertNotContains(dashboard, "Duplicate")

    def test_staff_inquiry_inbox_filters_and_prepares_email_replies(self):
        staff = get_user_model().objects.create_user(
            username="inbox-staff", password="test-password", is_staff=True
        )
        contact = ContactInquiry.objects.create(
            name="Maya Customer",
            email="maya@example.com",
            topic=ContactInquiry.TOPIC_PICKUP,
            message="Where should I collect my order?",
        )
        CateringInquiry.objects.create(
            name="Noam Events",
            email="noam@example.com",
            phone="0500000000",
            estimated_bagels=80,
            message="We are planning an office event.",
        )
        client = Client()
        client.force_login(staff)

        inbox = client.get(reverse("drops:staff_inquiries"))
        self.assertContains(inbox, "Inquiry inbox")
        self.assertContains(inbox, "Needs a reply")
        self.assertContains(inbox, "Potential bagels")
        self.assertContains(inbox, "Open in email app", count=2)

        filtered = client.get(
            reverse("drops:staff_inquiries"),
            {"q": "Maya", "kind": "customer", "status": "new"},
        )
        self.assertContains(filtered, "Maya Customer")
        self.assertNotContains(filtered, "Noam Events")
        self.assertContains(filtered, "Clear filters")

        return_path = reverse("drops:staff_inquiries") + "?kind=customer&status=new"
        update = client.post(
            reverse("drops:staff_contact_inquiry_status", args=[contact.id]),
            {"status": ContactInquiry.STATUS_REPLIED, "next": return_path},
        )
        self.assertRedirects(update, return_path, fetch_redirect_response=False)
        contact.refresh_from_db()
        self.assertEqual(contact.status, ContactInquiry.STATUS_REPLIED)

    def test_previous_drops_have_their_own_paginator(self):
        for index in range(7):
            Drop.objects.create(
                name=f"Previous Drop {index}",
                status=Drop.STATUS_CLOSED,
                opens_at=self.drop.opens_at - timedelta(days=index + 8),
                closes_at=self.drop.closes_at - timedelta(days=index + 8),
                pickup_starts_at=self.drop.pickup_starts_at - timedelta(days=index + 8),
                pickup_ends_at=self.drop.pickup_ends_at - timedelta(days=index + 8),
                pickup_location=self.drop.pickup_location,
                bagel_capacity=72,
                max_bagels_per_order=12,
            )
        staff = get_user_model().objects.create_user(username="drop-history", is_staff=True)
        client = Client()
        client.force_login(staff)

        response = client.get(reverse("drops:staff_dashboard"), {"previous_page": 2})

        self.assertEqual(response.context["previous_drops"].paginator.num_pages, 2)
        self.assertEqual(response.context["previous_drops"].number, 2)

    def test_branded_staff_login_accepts_staff_and_rejects_customers(self):
        staff = get_user_model().objects.create_user(
            username="avi-login", password="test-password", is_staff=True
        )
        customer = get_user_model().objects.create_user(
            username="customer-login", password="test-password"
        )
        client = Client()

        page = client.get(reverse("drops:staff_login"))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Good to see you, Avi.")

        rejected = client.post(
            reverse("drops:staff_login"),
            {"username": customer.username, "password": "test-password"},
        )
        self.assertEqual(rejected.status_code, 200)
        self.assertContains(rejected, "does not have staff access")
        self.assertNotIn("_auth_user_id", client.session)

        destination = reverse("drops:staff_orders")
        signed_in = client.post(
            reverse("drops:staff_login"),
            {
                "username": staff.username,
                "password": "test-password",
                "next": destination,
            },
        )
        self.assertRedirects(signed_in, destination)

        signed_out = client.post(reverse("drops:staff_logout"))
        self.assertRedirects(signed_out, reverse("drops:staff_login"))
        self.assertNotIn("_auth_user_id", client.session)

    def test_staff_can_delete_an_empty_draft_drop(self):
        draft = Drop.objects.create(
            name="Accidental Drop",
            status=Drop.STATUS_DRAFT,
            opens_at=self.drop.opens_at + timedelta(days=7),
            closes_at=self.drop.closes_at + timedelta(days=7),
            pickup_starts_at=self.drop.pickup_starts_at + timedelta(days=7),
            pickup_ends_at=self.drop.pickup_ends_at + timedelta(days=7),
            pickup_location=self.drop.pickup_location,
            bagel_capacity=75,
            max_bagels_per_order=4,
        )
        DropProduct.objects.create(drop=draft, product=self.plain)
        staff = get_user_model().objects.create_user(username="drop-deleter", is_staff=True)
        client = Client()
        client.force_login(staff)

        confirmation = client.get(reverse("drops:staff_delete", args=[draft.id]))
        self.assertContains(confirmation, "permanently delete")
        response = client.post(reverse("drops:staff_delete", args=[draft.id]))

        self.assertRedirects(response, reverse("drops:staff_dashboard"))
        self.assertFalse(Drop.objects.filter(pk=draft.id).exists())

    def test_staff_lists_are_paginated_and_excel_exports_open(self):
        NewsletterSubscriber.objects.bulk_create([
            NewsletterSubscriber(email=f"person{index:02d}@example.com")
            for index in range(30)
        ])
        staff = get_user_model().objects.create_user(username="exporter", is_staff=True)
        client = Client()
        client.force_login(staff)

        listing = client.get(reverse("drops:staff_subscribers"), {"page": 2})
        self.assertEqual(listing.context["page_obj"].paginator.num_pages, 3)
        self.assertEqual(len(listing.context["subscribers"]), 10)
        self.assertContains(listing, "Page 2 of 3")

        filtered = client.get(
            reverse("drops:staff_subscribers"),
            {"q": "person01", "status": "active"},
        )
        self.assertEqual(filtered.context["page_obj"].paginator.count, 1)
        self.assertEqual(filtered.context["selected_status"], "active")

        order_defaults = {
            "customer_name": "Repeat Buyer",
            "phone": "0501234567",
            "fulfillment_type": Order.FULFILLMENT_PICKUP,
            "payment_method": Order.PAYMENT_PAY_ON_PICKUP,
            "status": Order.STATUS_PAID,
            "drop": self.drop,
            "bagel_quantity": 1,
            "total_cents": 1200,
        }
        Order.objects.create(number="ABREPEAT001", email="PERSON01@example.com", **order_defaults)
        Order.objects.create(number="ABREPEAT002", email="person01@example.com", **order_defaults)

        customer_subscriber = client.get(
            reverse("drops:staff_subscribers"), {"q": "person01@example.com"}
        )
        self.assertTrue(customer_subscriber.context["subscribers"][0].is_customer)
        self.assertContains(customer_subscriber, "Customer")

        repeat_customers = client.get(
            reverse("drops:staff_customers"), {"customer_type": "repeat"}
        )
        self.assertEqual(repeat_customers.context["page_obj"].paginator.count, 1)
        self.assertEqual(repeat_customers.context["customers"][0]["order_count"], 2)
        self.assertEqual(repeat_customers.context["selected_customer_type"], "repeat")

        export = client.get(reverse("drops:staff_subscribers_excel"))
        self.assertEqual(
            export["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        workbook = load_workbook(BytesIO(export.content), read_only=True)
        self.assertEqual(workbook["Subscribers"].max_row, 31)

    def test_staff_products_support_catalog_filters_and_mobile_table_wrapper(self):
        hidden_extra = Product.objects.create(
            category=self.plain.category,
            name="Apricot Jam",
            name_en="Apricot Jam",
            slug="apricot-jam-test",
            price_cents=2800,
            product_type=Product.TYPE_EXTRA,
            is_active=False,
        )
        staff = get_user_model().objects.create_user(username="catalog-manager", is_staff=True)
        client = Client()
        client.force_login(staff)

        response = client.get(
            reverse("drops:staff_products"),
            {"status": "hidden", "type": "extra", "q": "Apricot"},
        )
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertEqual(response.context["products"][0], hidden_extra)
        self.assertEqual(response.context["selected_status"], "hidden")
        self.assertEqual(response.context["selected_type"], "extra")
        self.assertContains(response, 'class="table-responsive staff-table-card')
        self.assertContains(response, 'tabindex="0"')

        export = client.get(
            reverse("drops:staff_products_excel"),
            {"status": "hidden", "type": "extra"},
        )
        workbook = load_workbook(BytesIO(export.content), read_only=True)
        self.assertEqual(workbook["Products"].max_row, 2)

    def test_flash_messages_are_closable_and_auto_dismiss(self):
        staff = get_user_model().objects.create_user(username="messenger", is_staff=True)
        client = Client()
        client.force_login(staff)
        response = client.post(
            reverse("drops:staff_action", args=[self.drop.id]),
            {"action": "extend", "hours": 1},
            follow=True,
        )
        self.assertContains(response, 'data-auto-dismiss="6000"')
        self.assertContains(response, "btn-close")

    def test_staff_can_set_an_exact_ordering_cutoff(self):
        staff = get_user_model().objects.create_user(username="cutoff-editor", is_staff=True)
        client = Client()
        client.force_login(staff)
        new_cutoff = timezone.localtime(self.drop.closes_at + timedelta(minutes=30)).replace(
            second=0, microsecond=0
        )

        response = client.post(
            reverse("drops:staff_action", args=[self.drop.id]),
            {"action": "set_cutoff", "closes_at": new_cutoff.strftime("%Y-%m-%dT%H:%M")},
        )

        self.assertRedirects(response, reverse("drops:staff_detail", args=[self.drop.id]))
        self.drop.refresh_from_db()
        self.assertEqual(timezone.localtime(self.drop.closes_at), new_cutoff)

    def test_drop_email_actions_are_sent_once(self):
        NewsletterSubscriber.objects.bulk_create([
            NewsletterSubscriber(email="first@example.com"),
            NewsletterSubscriber(email="second@example.com"),
        ])
        Order.objects.create(
            number="ABREADY001",
            customer_name="Ready Customer",
            email="ready@example.com",
            phone="0500000000",
            fulfillment_type=Order.FULFILLMENT_PICKUP,
            payment_method=Order.PAYMENT_PAY_ON_PICKUP,
            status=Order.STATUS_PAID,
            total_cents=6500,
            bagel_quantity=6,
            drop=self.drop,
        )
        staff = get_user_model().objects.create_user(username="email-operator", is_staff=True)
        client = Client()
        client.force_login(staff)

        closing_url = reverse(
            "drops:staff_email", args=[self.drop.id, DropEmailCampaign.TYPE_CLOSING_SOON]
        )
        ready_url = reverse(
            "drops:staff_email", args=[self.drop.id, DropEmailCampaign.TYPE_ORDERS_READY]
        )
        client.post(closing_url)
        client.post(closing_url)
        client.post(ready_url)
        client.post(ready_url)

        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(self.drop.email_campaigns.count(), 2)
        self.assertEqual(
            self.drop.email_campaigns.get(
                campaign_type=DropEmailCampaign.TYPE_CLOSING_SOON
            ).recipient_count,
            2,
        )
        self.assertEqual(
            self.drop.email_campaigns.get(
                campaign_type=DropEmailCampaign.TYPE_ORDERS_READY
            ).recipient_count,
            1,
        )

    def test_demo_seed_is_complete_and_idempotent(self):
        call_command("seed_demo_data", verbosity=0)
        call_command("seed_demo_data", verbosity=0)
        self.assertEqual(Product.objects.filter(slug__in=[
            "plain", "sesame", "poppy", "onion", "everything", "mediterranean",
            "zaatar", "cinnamon-raisin", "jalapeno-cheddar",
        ]).count(), 9)
        self.assertTrue(Category.objects.filter(slug="cream-cheese", is_active=True).exists())
        self.assertTrue(Category.objects.filter(slug="jams", is_active=True).exists())
        self.assertEqual(
            Product.objects.filter(
                slug__in=[
                    "plain-cream-cheese", "scallion-cream-cheese",
                    "strawberry-jam", "seasonal-jam",
                ],
                product_type=Product.TYPE_EXTRA,
            ).count(),
            4,
        )
        self.assertEqual(Order.objects.filter(number__startswith="DEMO").count(), 20)
        self.assertEqual(
            NewsletterSubscriber.objects.filter(email__startswith="demo.customer").count(), 20
        )
        self.assertEqual(Drop.objects.filter(name="Demo Bagel Drop").count(), 1)
        self.assertEqual(Post.objects.filter(slug__startswith="demo-").count(), 3)

    def test_staff_cannot_delete_a_published_drop(self):
        staff = get_user_model().objects.create_user(username="careful-deleter", is_staff=True)
        client = Client()
        client.force_login(staff)

        confirmation = client.get(reverse("drops:staff_delete", args=[self.drop.id]))
        self.assertContains(confirmation, "Close this Drop before deleting it")
        response = client.post(
            reverse("drops:staff_delete", args=[self.drop.id]),
            follow=True,
        )

        self.assertTrue(Drop.objects.filter(pk=self.drop.id).exists())
        self.assertContains(response, "Close this Drop before deleting it")

    def test_staff_can_add_product_using_shekel_prices(self):
        staff = get_user_model().objects.create_user(username="product-owner", is_staff=True)
        client = Client()
        client.force_login(staff)
        response = client.post(
            reverse("drops:staff_product_create"),
            {
                "category": self.plain.category_id,
                "name_en": "Weekly Special",
                "name_he": "",
                "description_en": "A rotating special.",
                "description_he": "",
                "product_type": Product.TYPE_BAGEL,
                "price_ils": "99.00",
                "specialty_upcharge_ils": "2.50",
                "is_active": "on",
            },
        )
        self.assertRedirects(response, reverse("drops:staff_products"))
        product = Product.objects.get(name_en="Weekly Special")
        self.assertEqual(product.price_cents, 1450)
        self.assertEqual(product.specialty_upcharge_cents, 250)

    def test_staff_extra_keeps_an_independent_price(self):
        staff = get_user_model().objects.create_user(username="extras-owner", is_staff=True)
        client = Client()
        client.force_login(staff)
        response = client.post(
            reverse("drops:staff_product_create"),
            {
                "category": self.plain.category_id,
                "name_en": "Apricot Jam",
                "name_he": "",
                "description_en": "Small batch jam.",
                "description_he": "",
                "product_type": Product.TYPE_EXTRA,
                "price_ils": "18.00",
                "specialty_upcharge_ils": "9.00",
                "is_active": "on",
            },
        )
        self.assertRedirects(response, reverse("drops:staff_products"))
        product = Product.objects.get(name_en="Apricot Jam")
        self.assertEqual(product.price_cents, 1800)
        self.assertEqual(product.specialty_upcharge_cents, 0)

    def test_staff_can_create_and_publish_a_blog_post(self):
        staff = get_user_model().objects.create_user(username="blog-owner", is_staff=True)
        client = Client()
        client.force_login(staff)
        published_at = timezone.localtime(timezone.now()).replace(second=0, microsecond=0)
        response = client.post(
            reverse("drops:staff_blog_post_create"),
            {
                "category": "",
                "title_en": "A fresh test post",
                "excerpt_en": "News from the bakery.",
                "content_en": "This is the full story from the bakery.",
                "title_he": "",
                "excerpt_he": "",
                "content_he": "",
                "status": Post.STATUS_PUBLISHED,
                "published_at": published_at.strftime("%Y-%m-%dT%H:%M"),
            },
        )
        post = Post.objects.get(title_en="A fresh test post")
        self.assertRedirects(response, reverse("drops:staff_blog_posts"))
        self.assertEqual(
            client.get(reverse("drops:staff_blog_post_edit", args=[post.id])).status_code,
            200,
        )
        self.assertEqual(Client().get(post.get_absolute_url()).status_code, 200)

    def test_blog_content_is_sanitized_before_saving(self):
        staff = get_user_model().objects.create_user(username="safe-editor", is_staff=True)
        client = Client()
        client.force_login(staff)
        published_at = timezone.localtime(timezone.now()).replace(second=0, microsecond=0)

        response = client.post(
            reverse("drops:staff_blog_post_create"),
            {
                "category": "",
                "title_en": "Safe article",
                "excerpt_en": "A safe summary.",
                "content_en": '<h2>Hello</h2><script>alert(1)</script><a href="javascript:alert(2)">Bad link</a>',
                "title_he": "",
                "excerpt_he": "",
                "content_he": "",
                "status": Post.STATUS_PUBLISHED,
                "published_at": published_at.strftime("%Y-%m-%dT%H:%M"),
            },
        )

        self.assertRedirects(response, reverse("drops:staff_blog_posts"))
        content = Post.objects.get(title_en="Safe article").content_en
        self.assertIn("<h2>Hello</h2>", content)
        self.assertNotIn("<script", content)
        self.assertNotIn("javascript:", content)

    def test_staff_can_upload_an_inline_blog_image(self):
        staff = get_user_model().objects.create_user(username="image-editor", is_staff=True)
        client = Client()
        client.force_login(staff)
        image_buffer = BytesIO()
        Image.new("RGB", (4, 4), color="#f2c9a9").save(image_buffer, format="PNG")
        upload = SimpleUploadedFile("article.png", image_buffer.getvalue(), content_type="image/png")

        response = client.post(
            reverse("drops:staff_blog_image_upload"),
            {"upload": upload},
        )

        self.assertEqual(response.status_code, 200)
        url = response.json()["url"]
        self.assertTrue(url.startswith("/media/blog/inline/"))
        stored_name = url.removeprefix("/media/")
        self.assertTrue(default_storage.exists(stored_name))
        default_storage.delete(stored_name)

    def test_inline_blog_image_upload_requires_staff(self):
        response = Client().post(reverse("drops:staff_blog_image_upload"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("drops:staff_login"), response.url)

    def test_blog_form_loads_pinned_ckeditor(self):
        staff = get_user_model().objects.create_user(username="rich-editor", is_staff=True)
        client = Client()
        client.force_login(staff)

        response = client.get(reverse("drops:staff_blog_post_create"))

        self.assertContains(response, "/ckeditor5/43.3.1/ckeditor5.umd.js")
        self.assertContains(response, "staff-blog-editor.js")
        self.assertNotContains(response, "needs a CKEditor license key")

    def test_staff_can_update_bagel_deal_prices(self):
        staff = get_user_model().objects.create_user(username="pricing-owner", is_staff=True)
        client = Client()
        client.force_login(staff)
        tiers = list(BagelPriceTier.objects.order_by("quantity"))
        data = {
            "form-TOTAL_FORMS": len(tiers),
            "form-INITIAL_FORMS": len(tiers),
            "form-MIN_NUM_FORMS": 0,
            "form-MAX_NUM_FORMS": 1000,
        }
        for index, tier in enumerate(tiers):
            data.update({
                f"form-{index}-id": tier.id,
                f"form-{index}-quantity": tier.quantity,
                f"form-{index}-price_ils": (
                    "13.00" if tier.quantity == 1
                    else "64.00" if tier.quantity == 6
                    else f"{tier.price_cents / 100:.2f}"
                ),
                f"form-{index}-is_active": "on",
            })
        response = client.post(reverse("drops:staff_pricing"), data)
        self.assertRedirects(response, reverse("drops:staff_pricing"))
        self.assertEqual(BagelPriceTier.objects.get(quantity=1).price_cents, 1300)
        self.assertEqual(BagelPriceTier.objects.get(quantity=6).price_cents, 6400)
        self.plain.refresh_from_db()
        self.jalapeno.refresh_from_db()
        self.assertEqual(self.plain.price_cents, 1300)
        self.assertEqual(self.jalapeno.price_cents, 1600)

    def test_staff_can_send_one_drop_announcement(self):
        NewsletterSubscriber.objects.create(email="subscriber@example.com")
        staff = get_user_model().objects.create_user(username="announcer", is_staff=True)
        client = Client()
        client.force_login(staff)
        url = reverse("drops:staff_announcement", args=[self.drop.id])
        self.assertEqual(client.get(url).status_code, 200)
        self.assertRedirects(client.post(url), reverse("drops:staff_detail", args=[self.drop.id]))
        self.assertEqual(DropAnnouncement.objects.get(drop=self.drop).recipient_count, 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/en/drops/order/", mail.outbox[0].body)
        client.post(url)
        self.assertEqual(DropAnnouncement.objects.filter(drop=self.drop).count(), 1)

    def test_scheduled_drop_announcement_links_to_homepage_countdown(self):
        self.drop.opens_at = timezone.now() + timedelta(days=1)
        self.drop.closes_at = timezone.now() + timedelta(days=2)
        self.drop.pickup_starts_at = timezone.now() + timedelta(days=2, hours=1)
        self.drop.pickup_ends_at = timezone.now() + timedelta(days=2, hours=3)
        self.drop.save()
        NewsletterSubscriber.objects.create(email="waiting@example.com")
        staff = get_user_model().objects.create_user(username="prelaunch-announcer", is_staff=True)
        client = Client()
        client.force_login(staff)

        homepage = client.get(reverse("pages:home"))
        self.assertContains(homepage, "Ordering starts in")
        self.assertContains(homepage, "Email me before the Drop")
        self.assertNotContains(homepage, "bagel-header-1.jpg")

        client.post(reverse("drops:staff_announcement", args=[self.drop.id]))
        self.assertIn("See the countdown:", mail.outbox[0].body)
        self.assertNotIn("/en/drops/order/", mail.outbox[0].body)

    def test_staff_cancel_action_releases_capacity(self):
        customer = Client()
        self._add(customer, self.plain, 6)
        self._checkout(customer)
        order = Order.objects.get()
        staff = get_user_model().objects.create_user(username="owner", is_staff=True)
        client = Client()
        client.force_login(staff)
        response = client.post(
            reverse("drops:staff_order_status", args=[self.drop.id, order.id]),
            {"status": Order.STATUS_CANCELED},
        )
        self.assertRedirects(response, reverse("drops:staff_detail", args=[self.drop.id]))
        order.capacity_reservation.refresh_from_db()
        self.assertEqual(order.capacity_reservation.status, DropReservation.STATUS_RELEASED)

    def test_staff_order_workspace_replaces_admin_order_link(self):
        customer = Client()
        self._add(customer, self.plain, 2)
        self._checkout(customer)
        order = Order.objects.get()
        staff = get_user_model().objects.create_user(username="order-manager", is_staff=True)
        client = Client()
        client.force_login(staff)

        listing = client.get(reverse("drops:staff_orders"), {"q": order.number})
        self.assertContains(listing, order.number)
        self.assertContains(listing, reverse("drops:staff_order_detail", args=[order.id]))
        detail = client.get(reverse("drops:staff_order_detail", args=[order.id]))
        self.assertContains(detail, "Test Customer")
        self.assertContains(detail, "2 × Plain")

        response = client.post(
            reverse("drops:staff_order_status", args=[self.drop.id, order.id]),
            {"status": Order.STATUS_READY, "return": "order"},
        )
        self.assertRedirects(response, reverse("drops:staff_order_detail", args=[order.id]))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_READY)

    def test_checkout_get_redirects_when_cart_exceeds_order_cap(self):
        client = Client()
        self._add(client, self.plain, 13)
        response = client.get(reverse("checkout:checkout"))
        self.assertRedirects(response, reverse("cart:detail"))
        cart = client.get(reverse("cart:detail"))
        self.assertContains(cart, "maximum of 12 bagels")

    def test_canceled_order_cannot_be_reactivated_if_capacity_was_resold(self):
        self.drop.bagel_capacity = 6
        self.drop.max_bagels_per_order = 6
        self.drop.save()
        first_customer = Client()
        self._add(first_customer, self.plain, 6)
        self._checkout(first_customer)
        first_order = Order.objects.get()
        first_order.status = Order.STATUS_CANCELED
        first_order.save()

        second_customer = Client()
        self._add(second_customer, self.plain, 6)
        self._checkout(second_customer)

        staff = get_user_model().objects.create_user(username="capacity-manager", is_staff=True)
        client = Client()
        client.force_login(staff)
        response = client.post(
            reverse("drops:staff_order_status", args=[self.drop.id, first_order.id]),
            {"status": Order.STATUS_READY, "return": "order"},
            follow=True,
        )
        first_order.refresh_from_db()
        self.assertEqual(first_order.status, Order.STATUS_CANCELED)
        self.assertContains(response, "cannot be reactivated")
        self.assertEqual(self.drop.remaining_bagels, 0)

    def test_drop_cannot_be_published_without_an_active_bagel(self):
        self.drop.status = Drop.STATUS_DRAFT
        self.drop.save()
        self.drop.product_entries.all().delete()
        staff = get_user_model().objects.create_user(username="publisher", is_staff=True)
        client = Client()
        client.force_login(staff)
        response = client.post(
            reverse("drops:staff_action", args=[self.drop.id]),
            {"action": "publish"},
            follow=True,
        )
        self.drop.refresh_from_db()
        self.assertEqual(self.drop.status, Drop.STATUS_DRAFT)
        self.assertContains(response, "Add at least one active bagel")

    def test_staff_can_create_drop_with_selected_products(self):
        staff = get_user_model().objects.create_user(username="creator", is_staff=True)
        client = Client()
        client.force_login(staff)
        start = timezone.localtime(timezone.now() + timedelta(days=14)).replace(second=0, microsecond=0)
        response = client.post(
            reverse("drops:staff_create"),
            {
                "name": "Future Drop",
                "status": Drop.STATUS_DRAFT,
                "opens_at": start.strftime("%Y-%m-%dT%H:%M"),
                "closes_at": (start + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"),
                "pickup_starts_at": (start + timedelta(days=1, hours=1)).strftime("%Y-%m-%dT%H:%M"),
                "pickup_ends_at": (start + timedelta(days=1, hours=3)).strftime("%Y-%m-%dT%H:%M"),
                "pickup_location": "Ben Yehuda 69, Tel Aviv",
                "bagel_capacity": 90,
                "max_bagels_per_order": 12,
                "products": [self.plain.id],
            },
        )
        created = Drop.objects.get(name="Future Drop")
        self.assertRedirects(response, reverse("drops:staff_detail", args=[created.id]))
        self.assertEqual(list(created.products.all()), [self.plain])

    def test_capacity_alerts_are_deduplicated(self):
        self.drop.bagel_capacity = 10
        self.drop.max_bagels_per_order = 10
        self.drop.save()
        client = Client()
        self._add(client, self.plain, 6)
        self._checkout(client)
        notify_owner_about_drop_capacity(self.drop)
        notify_owner_about_drop_capacity(self.drop)
        self.assertEqual(
            DropAlert.objects.filter(alert_type=DropAlert.TYPE_LOW_CAPACITY).count(), 1
        )
