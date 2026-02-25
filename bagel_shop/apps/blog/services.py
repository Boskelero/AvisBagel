from django.utils import timezone

from .models import Post


def get_published_posts():
    return Post.objects.filter(status=Post.STATUS_PUBLISHED, published_at__lte=timezone.now())


def get_recent_posts(limit=3):
    return get_published_posts()[:limit]
