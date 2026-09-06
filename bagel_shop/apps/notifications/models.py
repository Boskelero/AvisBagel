from django.db import models


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email


class ContactInquiry(models.Model):
    STATUS_NEW = "new"
    STATUS_REPLIED = "replied"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_REPLIED, "Replied"),
        (STATUS_CLOSED, "Closed"),
    ]
    TOPIC_ORDER = "order"
    TOPIC_PICKUP = "pickup"
    TOPIC_PRODUCT = "product"
    TOPIC_FEEDBACK = "feedback"
    TOPIC_OTHER = "other"
    TOPIC_CHOICES = [
        (TOPIC_ORDER, "Existing order"),
        (TOPIC_PICKUP, "Pickup question"),
        (TOPIC_PRODUCT, "Product or ingredients"),
        (TOPIC_FEEDBACK, "Feedback"),
        (TOPIC_OTHER, "Something else"),
    ]

    name = models.CharField(max_length=160)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    topic = models.CharField(max_length=30, choices=TOPIC_CHOICES, default=TOPIC_OTHER)
    order_number = models.CharField(max_length=24, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.get_topic_display()}"


class CateringInquiry(models.Model):
    STATUS_NEW = "new"
    STATUS_CONTACTED = "contacted"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_CONTACTED, "Contacted"),
        (STATUS_CLOSED, "Closed"),
    ]

    name = models.CharField(max_length=160)
    email = models.EmailField()
    phone = models.CharField(max_length=40)
    event_date = models.DateField(null=True, blank=True)
    estimated_bagels = models.PositiveIntegerField(null=True, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.created_at:%Y-%m-%d}"


class DropAlert(models.Model):
    TYPE_LOW_CAPACITY = "low_capacity"
    TYPE_SOLD_OUT = "sold_out"
    TYPE_CHOICES = [
        (TYPE_LOW_CAPACITY, "Low capacity"),
        (TYPE_SOLD_OUT, "Sold out"),
    ]

    drop = models.ForeignKey("drops.Drop", on_delete=models.CASCADE, related_name="alert_events")
    alert_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    remaining_bagels = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["drop", "alert_type"], name="unique_drop_alert_type")
        ]

    def __str__(self):
        return f"{self.drop} — {self.get_alert_type_display()}"


class DropAnnouncement(models.Model):
    drop = models.OneToOneField("drops.Drop", on_delete=models.CASCADE, related_name="announcement")
    recipient_count = models.PositiveIntegerField(default=0)
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.drop} — {self.recipient_count} recipients"
