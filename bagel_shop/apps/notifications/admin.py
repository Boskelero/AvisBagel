from django.contrib import admin

from .models import (
    CateringInquiry,
    ContactInquiry,
    DropAlert,
    DropAnnouncement,
    NewsletterSubscriber,
)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("email",)


@admin.register(CateringInquiry)
class CateringInquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "event_date", "estimated_bagels", "status", "created_at")
    list_filter = ("status", "event_date", "created_at")
    list_editable = ("status",)
    search_fields = ("name", "email", "phone", "message")


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "topic", "order_number", "status", "created_at")
    list_filter = ("status", "topic", "created_at")
    list_editable = ("status",)
    search_fields = ("name", "email", "phone", "order_number", "message")


@admin.register(DropAlert)
class DropAlertAdmin(admin.ModelAdmin):
    list_display = ("drop", "alert_type", "remaining_bagels", "created_at")
    list_filter = ("alert_type", "created_at")
    readonly_fields = ("drop", "alert_type", "remaining_bagels", "created_at")


@admin.register(DropAnnouncement)
class DropAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("drop", "recipient_count", "sent_at")
    readonly_fields = ("drop", "recipient_count", "sent_at")
