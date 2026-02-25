from django.shortcuts import get_object_or_404, render

from .services import get_published_posts


def post_list(request):
    posts = get_published_posts()
    return render(request, "blog/post_list.html", {"posts": posts})


def post_detail(request, slug):
    post = get_object_or_404(get_published_posts(), slug=slug)
    return render(request, "blog/post_detail.html", {"post": post})
