from decouple import config

from .base import *  # noqa: F403

DEBUG = False

SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default=config("BUCKET", default=""))
AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default=config("ENDPOINT", default=""))
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default=config("ACCESS_KEY_ID", default=""))
AWS_SECRET_ACCESS_KEY = config(
    "AWS_SECRET_ACCESS_KEY", default=config("SECRET_ACCESS_KEY", default="")
)
AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default=config("REGION", default="auto"))
AWS_S3_SIGNATURE_VERSION = config("AWS_S3_SIGNATURE_VERSION", default="s3v4")
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = config("AWS_QUERYSTRING_AUTH", default=True, cast=bool)
AWS_QUERYSTRING_EXPIRE = config("AWS_QUERYSTRING_EXPIRE", default=86400, cast=int)
AWS_S3_FILE_OVERWRITE = False
AWS_S3_ADDRESSING_STYLE = config("AWS_S3_ADDRESSING_STYLE", default="virtual")

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "endpoint_url": AWS_S3_ENDPOINT_URL,
            "region_name": AWS_S3_REGION_NAME,
            "signature_version": AWS_S3_SIGNATURE_VERSION,
            "addressing_style": AWS_S3_ADDRESSING_STYLE,
            "default_acl": AWS_DEFAULT_ACL,
            "querystring_auth": AWS_QUERYSTRING_AUTH,
            "querystring_expire": AWS_QUERYSTRING_EXPIRE,
            "file_overwrite": AWS_S3_FILE_OVERWRITE,
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
