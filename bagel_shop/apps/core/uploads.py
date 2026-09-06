from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError


ALLOWED_IMAGE_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


def validate_image_upload(uploaded_file):
    """Validate an uploaded raster image and return its normalized extension."""
    max_bytes = getattr(settings, "MAX_IMAGE_UPLOAD_BYTES", 8 * 1024 * 1024)
    if uploaded_file.size > max_bytes:
        raise ValidationError(
            f"Image files must be smaller than {max_bytes // (1024 * 1024)} MB."
        )

    original_position = uploaded_file.tell()
    try:
        image = Image.open(uploaded_file)
        image_format = image.format
        image.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValidationError("Upload a valid JPG, PNG, or WebP image.") from None
    finally:
        uploaded_file.seek(original_position)

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError("Only JPG, PNG, and WebP images are supported.")
    return ALLOWED_IMAGE_FORMATS[image_format]
