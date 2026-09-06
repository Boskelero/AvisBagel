from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase
from django.urls import reverse

from bagel_shop.storage import PrivateMediaStorage


class MediaFileTests(TestCase):
    def setUp(self):
        self.name = default_storage.save(
            "test-media/sample image.png", ContentFile(b"not-a-real-png")
        )

    def tearDown(self):
        default_storage.delete(self.name)

    def test_media_file_is_streamed_with_cache_headers(self):
        response = self.client.get(reverse("media_file", kwargs={"name": self.name}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertEqual(response["Cache-Control"], "public, max-age=31536000, immutable")
        self.assertEqual(b"".join(response.streaming_content), b"not-a-real-png")

    def test_missing_media_file_returns_404(self):
        response = self.client.get(
            reverse("media_file", kwargs={"name": "missing/image.png"})
        )

        self.assertEqual(response.status_code, 404)

    def test_path_traversal_is_rejected(self):
        response = self.client.get("/media/folder/../secret.txt")

        self.assertEqual(response.status_code, 404)


class PrivateMediaStorageTests(TestCase):
    def test_storage_returns_stable_encoded_application_url(self):
        storage = PrivateMediaStorage(
            bucket_name="private-media",
            endpoint_url="https://example.invalid",
            access_key="test",
            secret_key="test",
        )

        self.assertEqual(
            storage.url("blog/My photo.png"),
            "/media/blog/My%20photo.png",
        )
