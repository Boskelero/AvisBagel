from urllib.parse import quote

from django.conf import settings
from storages.backends.s3 import S3Storage


class PrivateMediaStorage(S3Storage):
    """Store media privately while exposing stable, application-served URLs."""

    def url(self, name, parameters=None, expire=None, http_method=None):
        encoded_name = quote(str(name).lstrip("/"), safe="/")
        return f"{settings.MEDIA_URL.rstrip('/')}/{encoded_name}"
