from django.test import TestCase
from django.urls import reverse

from bagel_shop.apps.core.models import PageMetadata
from bagel_shop.apps.notifications.models import CateringInquiry, ContactInquiry


class CateringInquiryTests(TestCase):
    def test_static_page_metadata_controls_title_and_description(self):
        PageMetadata.objects.create(
            page_key=PageMetadata.PAGE_HOME,
            meta_title="Fresh Bagel Drops in Tel Aviv",
            meta_description="Order hand-rolled Abu Avi bagels from the next limited Drop.",
        )
        response = self.client.get(reverse("pages:home"))
        self.assertContains(response, "<title>Fresh Bagel Drops in Tel Aviv</title>", html=True)
        self.assertContains(
            response,
            '<meta name="description" content="Order hand-rolled Abu Avi bagels from the next limited Drop.">',
            html=True,
        )

    def test_homepage_has_faq_and_drop_notification_destination(self):
        response = self.client.get(reverse("pages:home"))
        self.assertContains(response, "Frequently asked questions")
        self.assertContains(response, "What is a bagel Drop?")
        self.assertContains(response, 'href="#drop-notify"', count=2)
        self.assertContains(response, 'id="drop-notify"')
        self.assertContains(response, "bagel-header-1.jpg")
        self.assertContains(response, "bagel-header-2.jpg")
        self.assertContains(response, "abu-avi-chef-badge.png")
        self.assertContains(response, reverse("pages:catering"))
        self.assertNotContains(response, "Order now")

    def test_visible_page_copy_uses_managed_content(self):
        PageMetadata.objects.update_or_create(
            page_key=PageMetadata.PAGE_BLOG,
            defaults={
                "heading_en": "Notes from Avi's oven",
                "intro_en": "Fresh stories from each weekly bake.",
                "content_en": "<p>Meet the people and ingredients behind every Drop.</p>",
            },
        )

        response = self.client.get(reverse("blog:post_list"))

        self.assertContains(response, "Notes from Avi&#x27;s oven")
        self.assertContains(response, "Fresh stories from each weekly bake.")
        self.assertContains(response, "Meet the people and ingredients behind every Drop.")

    def test_catering_page_is_in_navigation_and_has_full_request_flow(self):
        response = self.client.get(reverse("pages:catering"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/en/catering/"')
        self.assertContains(response, "Bring better bagels to the table.")
        self.assertContains(response, "Plan my order")
        self.assertContains(response, "Pickup only for now")
        self.assertContains(response, "Send catering request")

    def test_customer_can_submit_regular_contact_message(self):
        response = self.client.post(
            reverse("pages:contact"),
            {
                "name": "Regular Customer",
                "email": "customer@example.com",
                "phone": "",
                "topic": ContactInquiry.TOPIC_PICKUP,
                "order_number": "AB123",
                "message": "Can someone else collect my order?",
            },
        )
        self.assertRedirects(response, reverse("pages:contact"))
        inquiry = ContactInquiry.objects.get()
        self.assertEqual(inquiry.topic, ContactInquiry.TOPIC_PICKUP)
        self.assertEqual(inquiry.status, ContactInquiry.STATUS_NEW)

    def test_customer_can_submit_large_order_inquiry(self):
        response = self.client.post(
            reverse("pages:catering"),
            {
                "name": "Large Order Customer",
                "email": "events@example.com",
                "phone": "0505551234",
                "event_date": "2026-10-10",
                "estimated_bagels": 48,
                "message": "Bagels for an office event.",
            },
        )
        self.assertRedirects(response, reverse("pages:catering"))
        inquiry = CateringInquiry.objects.get()
        self.assertEqual(inquiry.estimated_bagels, 48)
        self.assertEqual(inquiry.status, CateringInquiry.STATUS_NEW)
