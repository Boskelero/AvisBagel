import csv
from datetime import timedelta
from functools import partial
from uuid import uuid4

from django.contrib.admin.views.decorators import staff_member_required as admin_staff_member_required
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.forms import modelformset_factory
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from bagel_shop.apps.catalog.models import Category, Product
from bagel_shop.apps.blog.forms import StaffPostForm
from bagel_shop.apps.blog.models import Post
from bagel_shop.apps.core.models import PageMetadata
from bagel_shop.apps.core.uploads import validate_image_upload
from bagel_shop.apps.orders.models import Order, OrderItem
from bagel_shop.apps.cart.services import add_product_to_cart, clear_cart
from bagel_shop.apps.notifications.models import (
    CateringInquiry,
    ContactInquiry,
    NewsletterSubscriber,
)
from bagel_shop.apps.notifications.services import send_drop_announcement

from .forms import (
    BagelPriceTierForm,
    BagelPriceTierFormSet,
    CategoryForm,
    DropForm,
    ProductForm,
    PageMetadataForm,
)
from .exports import workbook_response
from .models import BagelPriceTier, Drop, DropProduct
from .services import get_current_drop


staff_member_required = partial(
    admin_staff_member_required,
    login_url="drops:staff_login",
)


@require_http_methods(["GET", "POST"])
def staff_login(request):
    next_url = request.POST.get("next") or request.GET.get("next", "")
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("drops:staff_dashboard")

    form = AuthenticationForm(request=request, data=request.POST or None)
    form.fields["username"].widget.attrs.update(
        {"class": "form-control", "autocomplete": "username", "autofocus": True}
    )
    form.fields["password"].widget.attrs.update(
        {"class": "form-control", "autocomplete": "current-password"}
    )
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        if not user.is_staff:
            form.add_error(None, "This account does not have staff access.")
        else:
            auth_login(request, user)
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("drops:staff_dashboard")

    return render(
        request,
        "drops/staff_login.html",
        {"form": form, "next": next_url},
    )


@require_POST
def staff_logout(request):
    auth_logout(request)
    messages.success(request, "You have been logged out securely.")
    return redirect("drops:staff_login")


def _production_totals(drop):
    rows = list(
        OrderItem.objects.filter(order__drop=drop)
        .exclude(order__status=Order.STATUS_CANCELED)
        .values("product_id_snapshot", "product_name")
        .annotate(quantity=Sum("quantity"))
        .order_by("product_name")
    )
    product_types = dict(
        Product.objects.filter(id__in=[row["product_id_snapshot"] for row in rows])
        .values_list("id", "product_type")
    )
    bagels, extras = [], []
    for row in rows:
        target = bagels if product_types.get(row["product_id_snapshot"]) == Product.TYPE_BAGEL else extras
        target.append(row)
    return bagels, extras


def _csv_safe(value):
    text = str(value or "")
    return f"'{text}" if text.startswith(("=", "+", "-", "@")) else text


def _paginate(request, items, per_page=25, page_param="page"):
    return Paginator(items, per_page).get_page(request.GET.get(page_param))


def _staff_orders_queryset(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    orders = (
        Order.objects.exclude(status=Order.STATUS_DRAFT)
        .select_related("drop")
        .prefetch_related("items")
        .order_by("-created_at")
    )
    if query:
        orders = orders.filter(
            Q(number__icontains=query)
            | Q(customer_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
        )
    allowed_statuses = [choice for choice in Order.STATUS_CHOICES if choice[0] != Order.STATUS_DRAFT]
    if status in {value for value, _ in allowed_statuses}:
        orders = orders.filter(status=status)
    else:
        status = ""
    return orders, query, status, allowed_statuses


def _customer_rows(query=""):
    orders = Order.objects.exclude(status=Order.STATUS_DRAFT).order_by("email", "-created_at")
    if query:
        orders = orders.filter(
            Q(customer_name__icontains=query) | Q(email__icontains=query) | Q(phone__icontains=query)
        )
    customers = {}
    for order in orders:
        key = order.email.strip().lower()
        customer = customers.setdefault(key, {
            "name": order.customer_name,
            "email": order.email,
            "phone": order.phone,
            "latest_order": order,
            "order_count": 0,
            "bagel_count": 0,
            "total_cents": 0,
        })
        customer["order_count"] += 1
        if order.status != Order.STATUS_CANCELED:
            customer["bagel_count"] += order.bagel_quantity
            customer["total_cents"] += order.total_cents
    return sorted(
        customers.values(), key=lambda customer: customer["latest_order"].created_at, reverse=True
    )


@require_http_methods(["GET", "POST"])
def order_current_drop(request):
    drop = get_current_drop()
    if not drop or not drop.is_ordering_open:
        messages.info(request, "There is no active Drop accepting orders right now.")
        return redirect("catalog:menu")
    entries = list(
        drop.product_entries.filter(is_available=True, product__is_active=True)
        .select_related("product")
        .prefetch_related("product__images")
        .order_by("sort_order", "product__name")
    )
    bagel_entries = [entry for entry in entries if entry.product.counts_toward_bagel_capacity]
    extra_entries = [entry for entry in entries if not entry.product.counts_toward_bagel_capacity]
    if request.method == "POST":
        selected = []
        bagel_quantity = 0
        for entry in entries:
            try:
                quantity = max(0, int(request.POST.get(f"product_{entry.product_id}", 0)))
            except (TypeError, ValueError):
                quantity = 0
            if quantity:
                selected.append((entry.product, quantity))
                if entry.product.counts_toward_bagel_capacity:
                    bagel_quantity += quantity
        if not selected:
            messages.error(request, "Choose at least one item.")
        elif bagel_quantity == 0:
            messages.error(request, "An order must include at least one bagel.")
        elif bagel_quantity > drop.max_bagels_per_order:
            messages.error(request, f"This Drop allows up to {drop.max_bagels_per_order} bagels per order.")
        elif bagel_quantity > drop.remaining_bagels:
            messages.error(request, f"Only {drop.remaining_bagels} bagels remain in this Drop.")
        else:
            clear_cart(request)
            for product, quantity in selected:
                add_product_to_cart(request, product, quantity)
            return redirect("cart:detail")
    pricing_tiers = list(
        BagelPriceTier.objects.filter(is_active=True)
        .values("quantity", "price_cents")
        .order_by("quantity")
    )
    return render(request, "drops/order_builder.html", {
        "drop": drop,
        "bagel_entries": bagel_entries,
        "extra_entries": extra_entries,
        "pricing_tiers": pricing_tiers,
    })


@staff_member_required
def staff_dashboard(request):
    drops = _paginate(request, Drop.objects.all().order_by("-pickup_starts_at"), per_page=12)
    new_inquiry_count = (
        CateringInquiry.objects.filter(status=CateringInquiry.STATUS_NEW).count()
        + ContactInquiry.objects.filter(status=ContactInquiry.STATUS_NEW).count()
    )
    return render(request, "drops/staff_dashboard.html", {
        "drops": drops,
        "subscriber_count": NewsletterSubscriber.objects.filter(is_active=True).count(),
        "new_inquiry_count": new_inquiry_count,
    })


@staff_member_required
def staff_orders(request):
    orders, query, status, allowed_statuses = _staff_orders_queryset(request)
    page_obj = _paginate(request, orders)
    return render(request, "drops/staff_orders.html", {
        "orders": page_obj,
        "page_obj": page_obj,
        "query": query,
        "selected_status": status,
        "status_choices": allowed_statuses,
    })


@staff_member_required
def staff_order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related("drop").prefetch_related("items"), pk=order_id
    )
    return render(request, "drops/staff_order_detail.html", {
        "order": order,
        "status_choices": [
            choice for choice in Order.STATUS_CHOICES if choice[0] != Order.STATUS_DRAFT
        ],
    })


@staff_member_required
def staff_customers(request):
    query = request.GET.get("q", "").strip()
    page_obj = _paginate(request, _customer_rows(query))
    return render(request, "drops/staff_customers.html", {
        "customers": page_obj, "page_obj": page_obj, "query": query
    })


@staff_member_required
def staff_products(request):
    query = request.GET.get("q", "").strip()
    show_all = request.GET.get("status") == "all"
    products = Product.objects.select_related("category").prefetch_related("images").order_by(
        "product_type", "name"
    )
    if not show_all:
        products = products.filter(is_active=True)
    if query:
        products = products.filter(Q(name_en__icontains=query) | Q(name_he__icontains=query))
    page_obj = _paginate(request, products)
    return render(request, "drops/staff_products.html", {
        "products": page_obj, "page_obj": page_obj, "query": query, "show_all": show_all
    })


@staff_member_required
def staff_blog_posts(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    posts = Post.objects.select_related("category").order_by("-published_at", "-created_at")
    if query:
        posts = posts.filter(
            Q(title_en__icontains=query)
            | Q(title_he__icontains=query)
            | Q(excerpt_en__icontains=query)
            | Q(excerpt_he__icontains=query)
        )
    if status in {Post.STATUS_DRAFT, Post.STATUS_PUBLISHED}:
        posts = posts.filter(status=status)
    else:
        status = ""
    page_obj = _paginate(request, posts, per_page=12)
    return render(request, "drops/staff_blog_posts.html", {
        "posts": page_obj,
        "page_obj": page_obj,
        "query": query,
        "selected_status": status,
        "status_choices": Post.STATUS_CHOICES,
    })


@staff_member_required
@require_http_methods(["GET", "POST"])
def staff_blog_post_create(request):
    form = StaffPostForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        post = form.save()
        messages.success(request, f"{post} was added to the blog.")
        return redirect("drops:staff_blog_posts")
    return render(request, "drops/staff_blog_post_form.html", {
        "form": form, "title": "Add blog post",
        "ckeditor_version": settings.CKEDITOR_VERSION,
    })


@staff_member_required
@require_http_methods(["GET", "POST"])
def staff_blog_post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = StaffPostForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{post} was updated.")
        return redirect("drops:staff_blog_posts")
    return render(request, "drops/staff_blog_post_form.html", {
        "form": form, "post": post, "title": f"Edit {post}",
        "ckeditor_version": settings.CKEDITOR_VERSION,
    })


@staff_member_required
@require_POST
def staff_blog_image_upload(request):
    uploaded_file = request.FILES.get("upload")
    if not uploaded_file:
        return JsonResponse({"error": {"message": "Choose an image to upload."}}, status=400)

    try:
        extension = validate_image_upload(uploaded_file)
    except ValidationError as exc:
        return JsonResponse({"error": {"message": exc.messages[0]}}, status=400)

    dated_path = timezone.localdate().strftime("%Y/%m")
    name = f"blog/inline/{dated_path}/{uuid4().hex}{extension}"
    try:
        stored_name = default_storage.save(name, uploaded_file)
    except (OSError, ValueError):
        return JsonResponse(
            {"error": {"message": "The image could not be stored. Please try again."}},
            status=503,
        )
    return JsonResponse({"url": default_storage.url(stored_name)})


@staff_member_required
@require_http_methods(["GET", "POST"])
def staff_product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        messages.success(request, f"{product} was added to the catalog.")
        return redirect("drops:staff_products")
    return render(request, "drops/staff_product_form.html", {"form": form, "title": "Add product"})


@staff_member_required
@require_http_methods(["GET", "POST"])
def staff_product_edit(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{product} was updated.")
        return redirect("drops:staff_products")
    return render(request, "drops/staff_product_form.html", {
        "form": form, "product": product, "title": f"Edit {product}"
    })


@staff_member_required
@require_http_methods(["GET", "POST"])
def staff_categories(request, category_id=None):
    category = get_object_or_404(Category, pk=category_id) if category_id else None
    form = CategoryForm(request.POST or None, instance=category)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        messages.success(request, f"Category {saved} saved.")
        return redirect("drops:staff_categories")
    return render(request, "drops/staff_categories.html", {
        "categories": Category.objects.annotate(product_count=Count("products")),
        "form": form,
        "editing_category": category,
    })


@staff_member_required
@require_http_methods(["GET", "POST"])
def staff_pricing(request):
    TierFormSet = modelformset_factory(
        BagelPriceTier,
        form=BagelPriceTierForm,
        formset=BagelPriceTierFormSet,
        extra=1,
        can_delete=True,
    )
    formset = TierFormSet(request.POST or None, queryset=BagelPriceTier.objects.order_by("quantity"))
    if request.method == "POST" and formset.is_valid():
        formset.save()
        messages.success(request, "Bagel deal pricing updated.")
        return redirect("drops:staff_pricing")
    return render(request, "drops/staff_pricing.html", {"formset": formset})


@staff_member_required
@require_http_methods(["GET", "POST"])
def staff_seo(request):
    for page_key, _ in PageMetadata.PAGE_CHOICES:
        PageMetadata.objects.get_or_create(page_key=page_key)
    MetadataFormSet = modelformset_factory(
        PageMetadata,
        form=PageMetadataForm,
        extra=0,
    )
    formset = MetadataFormSet(request.POST or None, queryset=PageMetadata.objects.all())
    if request.method == "POST" and formset.is_valid():
        formset.save()
        messages.success(request, "Page titles and descriptions updated.")
        return redirect("drops:staff_seo")
    return render(request, "drops/staff_seo.html", {"formset": formset})


@staff_member_required
def staff_inquiries(request):
    contact_page = _paginate(
        request, ContactInquiry.objects.all(), per_page=10, page_param="contact_page"
    )
    catering_page = _paginate(
        request, CateringInquiry.objects.all(), per_page=10, page_param="catering_page"
    )
    return render(request, "drops/staff_inquiries.html", {
        "contact_inquiries": contact_page,
        "catering_inquiries": catering_page,
        "contact_page": contact_page,
        "catering_page": catering_page,
    })


@staff_member_required
@require_POST
def staff_contact_inquiry_status(request, inquiry_id):
    inquiry = get_object_or_404(ContactInquiry, pk=inquiry_id)
    status = request.POST.get("status")
    if status in {value for value, _ in ContactInquiry.STATUS_CHOICES}:
        inquiry.status = status
        inquiry.save(update_fields=["status"])
        messages.success(request, "Customer message updated.")
    return redirect("drops:staff_inquiries")


@staff_member_required
@require_POST
def staff_inquiry_status(request, inquiry_id):
    inquiry = get_object_or_404(CateringInquiry, pk=inquiry_id)
    status = request.POST.get("status")
    if status in {value for value, _ in CateringInquiry.STATUS_CHOICES}:
        inquiry.status = status
        inquiry.save(update_fields=["status"])
        messages.success(request, "Inquiry updated.")
    return redirect("drops:staff_inquiries")


@staff_member_required
def staff_subscribers(request):
    page_obj = _paginate(request, NewsletterSubscriber.objects.all())
    return render(request, "drops/staff_subscribers.html", {
        "subscribers": page_obj, "page_obj": page_obj
    })


@staff_member_required
@require_POST
def staff_subscriber_toggle(request, subscriber_id):
    subscriber = get_object_or_404(NewsletterSubscriber, pk=subscriber_id)
    subscriber.is_active = not subscriber.is_active
    subscriber.save(update_fields=["is_active"])
    messages.success(request, "Subscriber status updated.")
    return redirect("drops:staff_subscribers")


@staff_member_required
@require_http_methods(["GET", "POST"])
def staff_drop_announcement(request, drop_id):
    drop = get_object_or_404(Drop, pk=drop_id)
    existing = getattr(drop, "announcement", None)
    if request.method == "POST":
        if drop.status != Drop.STATUS_PUBLISHED:
            messages.error(request, "Publish the Drop before announcing it.")
        elif existing:
            messages.info(request, "This Drop announcement has already been sent.")
        else:
            try:
                announcement, _ = send_drop_announcement(drop)
                messages.success(request, f"Announcement sent to {announcement.recipient_count} subscribers.")
            except Exception:
                messages.error(request, "The announcement could not be sent. Check the email configuration and try again.")
        return redirect("drops:staff_detail", drop_id=drop.id)
    return render(request, "drops/staff_announcement.html", {
        "drop": drop,
        "existing": existing,
        "subscriber_count": NewsletterSubscriber.objects.filter(is_active=True).count(),
    })


@staff_member_required
def staff_customer_detail(request, order_id):
    anchor = get_object_or_404(Order, pk=order_id)
    orders = Order.objects.filter(email__iexact=anchor.email).select_related("drop").prefetch_related("items")
    page_obj = _paginate(request, orders, per_page=10)
    return render(request, "drops/staff_customer_detail.html", {
        "customer": anchor, "orders": page_obj, "page_obj": page_obj
    })


@staff_member_required
@require_http_methods(["GET", "POST"])
def staff_drop_create(request):
    form = DropForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        drop = form.save()
        messages.success(request, "Drop created.")
        return redirect("drops:staff_detail", drop_id=drop.id)
    return render(request, "drops/staff_drop_form.html", {"form": form, "title": "Create Drop"})


@staff_member_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def staff_drop_edit(request, drop_id):
    drop = get_object_or_404(Drop.objects.select_for_update(), pk=drop_id)
    form = DropForm(request.POST or None, instance=drop)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Drop updated.")
        return redirect("drops:staff_detail", drop_id=drop.id)
    return render(request, "drops/staff_drop_form.html", {"form": form, "drop": drop, "title": "Edit Drop"})


@staff_member_required
@require_http_methods(["GET", "POST"])
def staff_drop_delete(request, drop_id):
    drop = get_object_or_404(Drop, pk=drop_id)
    blockers = []
    if drop.status == Drop.STATUS_PUBLISHED:
        blockers.append("Close this Drop before deleting it.")
    if drop.orders.exists() or drop.reservations.exists():
        blockers.append("Drops with orders or capacity reservations must be kept for customer history.")
    if hasattr(drop, "announcement"):
        blockers.append("This Drop was announced to subscribers and must be kept for communication history.")
    if request.method == "POST":
        if blockers:
            for blocker in blockers:
                messages.error(request, blocker)
            return redirect("drops:staff_detail", drop_id=drop.id)
        name = drop.name
        drop.delete()
        messages.success(request, f"{name} was permanently deleted.")
        return redirect("drops:staff_dashboard")
    return render(request, "drops/staff_drop_confirm_delete.html", {
        "drop": drop,
        "blockers": blockers,
    })


@staff_member_required
@require_POST
def staff_drop_duplicate(request, drop_id):
    source = get_object_or_404(Drop, pk=drop_id)
    with transaction.atomic():
        duplicate = Drop.objects.create(
            name=f"{source.name} — next week",
            status=Drop.STATUS_DRAFT,
            opens_at=source.opens_at + timedelta(days=7),
            closes_at=source.closes_at + timedelta(days=7),
            pickup_starts_at=source.pickup_starts_at + timedelta(days=7),
            pickup_ends_at=source.pickup_ends_at + timedelta(days=7),
            pickup_location=source.pickup_location,
            bagel_capacity=source.bagel_capacity,
            max_bagels_per_order=source.max_bagels_per_order,
        )
        DropProduct.objects.bulk_create([
            DropProduct(
                drop=duplicate,
                product=entry.product,
                is_available=entry.is_available,
                price_override_cents=entry.price_override_cents,
                sort_order=entry.sort_order,
            )
            for entry in source.product_entries.all()
        ])
    messages.success(request, "A draft for next week was created.")
    return redirect("drops:staff_edit", drop_id=duplicate.id)


@staff_member_required
@require_POST
@transaction.atomic
def staff_drop_action(request, drop_id):
    drop = get_object_or_404(Drop.objects.select_for_update(), pk=drop_id)
    action = request.POST.get("action")
    if action == "close":
        drop.status = Drop.STATUS_CLOSED
    elif action == "publish":
        if not drop.product_entries.filter(
            is_available=True,
            product__is_active=True,
            product__product_type=Product.TYPE_BAGEL,
        ).exists():
            messages.error(request, "Add at least one active bagel before publishing this Drop.")
            return redirect("drops:staff_detail", drop_id=drop.id)
        drop.status = Drop.STATUS_PUBLISHED
    elif action == "extend":
        try:
            hours = max(1, min(168, int(request.POST.get("hours", 1))))
        except (TypeError, ValueError):
            hours = 1
        drop.closes_at += timedelta(hours=hours)
    elif action == "capacity":
        try:
            drop.bagel_capacity = int(request.POST.get("capacity"))
        except (TypeError, ValueError):
            messages.error(request, "Enter a valid capacity.")
            return redirect("drops:staff_detail", drop_id=drop.id)
    else:
        messages.error(request, "Unknown Drop action.")
        return redirect("drops:staff_detail", drop_id=drop.id)
    try:
        drop.full_clean()
        drop.save()
        messages.success(request, "Drop updated.")
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    return redirect("drops:staff_detail", drop_id=drop.id)


@staff_member_required
@require_POST
@transaction.atomic
def staff_order_status(request, drop_id, order_id):
    order = get_object_or_404(
        Order.objects.select_for_update(), pk=order_id, drop_id=drop_id
    )
    drop = get_object_or_404(Drop.objects.select_for_update(), pk=drop_id)
    status = request.POST.get("status")
    allowed = {
        value for value, _ in Order.STATUS_CHOICES if value != Order.STATUS_DRAFT
    }
    if status not in allowed:
        messages.error(request, "Invalid order status.")
    elif (
        order.status == Order.STATUS_CANCELED
        and status != Order.STATUS_CANCELED
        and order.bagel_quantity > drop.remaining_bagels
    ):
        messages.error(
            request,
            f"Order {order.number} cannot be reactivated: only {drop.remaining_bagels} bagels remain.",
        )
    else:
        order.status = status
        order.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Order {order.number} updated.")
    if request.POST.get("return") == "order":
        return redirect("drops:staff_order_detail", order_id=order.id)
    return redirect("drops:staff_detail", drop_id=drop_id)


@staff_member_required
def staff_drop_detail(request, drop_id):
    drop = get_object_or_404(Drop, pk=drop_id)
    orders = list(drop.orders.prefetch_related("items").order_by("-created_at"))
    customer_counts = dict(
        Order.objects.filter(email__in=[order.email for order in orders])
        .values_list("email")
        .annotate(total=Count("id"))
    )
    for order in orders:
        order.customer_order_count = customer_counts.get(order.email, 1)
    bagel_totals, extra_totals = _production_totals(drop)
    page_obj = _paginate(request, orders)
    return render(
        request,
        "drops/staff_drop_detail.html",
        {
            "drop": drop,
            "orders": page_obj,
            "page_obj": page_obj,
            "bagel_totals": bagel_totals,
            "extra_totals": extra_totals,
        },
    )


@staff_member_required
def staff_orders_excel(request):
    orders, _, _, _ = _staff_orders_queryset(request)
    rows = []
    for order in orders:
        rows.append([
            order.number,
            order.customer_name,
            order.email,
            order.phone,
            order.drop.name if order.drop else "",
            order.get_status_display(),
            order.bagel_quantity,
            order.total_cents / 100,
            ", ".join(f"{item.product_name} × {item.quantity}" for item in order.items.all()),
            timezone.localtime(order.created_at).strftime("%Y-%m-%d %H:%M"),
        ])
    return workbook_response("orders.xlsx", [(
        "Orders",
        ["Order", "Customer", "Email", "Phone", "Drop", "Status", "Bagels", "Total ILS", "Items", "Created"],
        rows,
    )])


@staff_member_required
def staff_customers_excel(request):
    rows = [[
        customer["name"],
        customer["email"],
        customer["phone"],
        customer["order_count"],
        customer["bagel_count"],
        customer["total_cents"] / 100,
        timezone.localtime(customer["latest_order"].created_at).strftime("%Y-%m-%d %H:%M"),
    ] for customer in _customer_rows(request.GET.get("q", "").strip())]
    return workbook_response("customers.xlsx", [(
        "Customers",
        ["Customer", "Email", "Phone", "Orders", "Bagels", "Order value ILS", "Last order"],
        rows,
    )])


@staff_member_required
def staff_products_excel(request):
    products = Product.objects.select_related("category").order_by("product_type", "name")
    rows = [[
        product.name_en or product.name,
        str(product.category),
        product.get_product_type_display(),
        product.price_cents / 100,
        product.specialty_upcharge_cents / 100,
        "Active" if product.is_active else "Hidden",
        "Yes" if product.is_featured else "No",
    ] for product in products]
    return workbook_response("products.xlsx", [(
        "Products",
        ["Product", "Category", "Type", "Price ILS", "Deal upcharge ILS", "Status", "Featured"],
        rows,
    )])


@staff_member_required
def staff_subscribers_excel(request):
    rows = [[
        subscriber.email,
        "Active" if subscriber.is_active else "Inactive",
        timezone.localtime(subscriber.created_at).strftime("%Y-%m-%d %H:%M"),
    ] for subscriber in NewsletterSubscriber.objects.all()]
    return workbook_response("drop-subscribers.xlsx", [(
        "Subscribers", ["Email", "Status", "Joined"], rows
    )])


@staff_member_required
def staff_inquiries_excel(request):
    contact_rows = [[
        inquiry.name,
        inquiry.email,
        inquiry.phone,
        inquiry.get_topic_display(),
        inquiry.order_number,
        inquiry.message,
        inquiry.get_status_display(),
        timezone.localtime(inquiry.created_at).strftime("%Y-%m-%d %H:%M"),
    ] for inquiry in ContactInquiry.objects.all()]
    catering_rows = [[
        inquiry.name,
        inquiry.email,
        inquiry.phone,
        inquiry.event_date.isoformat() if inquiry.event_date else "",
        inquiry.estimated_bagels or "",
        inquiry.message,
        inquiry.get_status_display(),
        timezone.localtime(inquiry.created_at).strftime("%Y-%m-%d %H:%M"),
    ] for inquiry in CateringInquiry.objects.all()]
    return workbook_response("inquiries.xlsx", [
        ("Customer messages", ["Name", "Email", "Phone", "Topic", "Order", "Message", "Status", "Created"], contact_rows),
        ("Catering", ["Name", "Email", "Phone", "Event date", "Estimated bagels", "Message", "Status", "Created"], catering_rows),
    ])


@staff_member_required
def staff_drop_excel(request, drop_id):
    drop = get_object_or_404(Drop, pk=drop_id)
    rows = []
    for order in drop.orders.prefetch_related("items").order_by("created_at"):
        for item in order.items.all():
            rows.append([
                order.number,
                order.customer_name,
                order.email,
                order.phone,
                order.get_status_display(),
                item.product_name,
                item.quantity,
                order.bagel_quantity,
                order.total_cents / 100,
                timezone.localtime(order.created_at).strftime("%Y-%m-%d %H:%M"),
            ])
    return workbook_response(f"drop-{drop.id}-orders.xlsx", [(
        "Drop orders",
        ["Order", "Customer", "Email", "Phone", "Status", "Item", "Item quantity", "Total bagels", "Total ILS", "Created"],
        rows,
    )])


@staff_member_required
def staff_drop_csv(request, drop_id):
    drop = get_object_or_404(Drop, pk=drop_id)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="drop-{drop.id}-orders.csv"'
    writer = csv.writer(response)
    writer.writerow(["Order", "Customer", "Email", "Phone", "Status", "Item", "Quantity", "Total ILS"])
    for order in drop.orders.prefetch_related("items").order_by("created_at"):
        for item in order.items.all():
            writer.writerow([
                _csv_safe(order.number),
                _csv_safe(order.customer_name),
                _csv_safe(order.email),
                _csv_safe(order.phone),
                _csv_safe(order.get_status_display()),
                _csv_safe(item.product_name),
                item.quantity,
                f"{order.total_cents / 100:.2f}",
            ])
    return response


@staff_member_required
def staff_production_sheet(request, drop_id):
    drop = get_object_or_404(Drop, pk=drop_id)
    bagel_totals, extra_totals = _production_totals(drop)
    orders = drop.orders.exclude(status=Order.STATUS_CANCELED).order_by("customer_name")
    return render(request, "drops/staff_production_sheet.html", {
        "drop": drop,
        "bagel_totals": bagel_totals,
        "extra_totals": extra_totals,
        "orders": orders,
    })
