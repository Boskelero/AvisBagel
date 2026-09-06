import mimetypes

from botocore.exceptions import ClientError
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.http import require_GET


def healthcheck(request):
    return JsonResponse({"status": "ok"})


@require_GET
def media_file(request, name):
    """Stream a public media asset from the configured private storage backend."""
    normalized_name = str(name).replace("\\", "/").lstrip("/")
    if not normalized_name or ".." in normalized_name.split("/"):
        raise Http404

    try:
        stored_file = default_storage.open(normalized_name, "rb")
    except (ClientError, FileNotFoundError, OSError, ValueError):
        raise Http404 from None

    content_type, _ = mimetypes.guess_type(normalized_name)
    response = FileResponse(
        stored_file,
        content_type=content_type or "application/octet-stream",
        filename=normalized_name.rsplit("/", 1)[-1],
        as_attachment=False,
    )
    response["Cache-Control"] = "public, max-age=31536000, immutable"
    response["X-Content-Type-Options"] = "nosniff"
    return response
