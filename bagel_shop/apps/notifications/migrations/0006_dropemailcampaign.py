import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("drops", "0003_sync_bagel_product_prices"),
        ("notifications", "0005_contactinquiry"),
    ]

    operations = [
        migrations.CreateModel(
            name="DropEmailCampaign",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "campaign_type",
                    models.CharField(
                        choices=[
                            ("closing_soon", "One-hour closing reminder"),
                            ("orders_ready", "Orders ready"),
                        ],
                        max_length=30,
                    ),
                ),
                ("recipient_count", models.PositiveIntegerField(default=0)),
                ("sent_at", models.DateTimeField(auto_now_add=True)),
                (
                    "drop",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="email_campaigns",
                        to="drops.drop",
                    ),
                ),
            ],
            options={"ordering": ["-sent_at"]},
        ),
        migrations.AddConstraint(
            model_name="dropemailcampaign",
            constraint=models.UniqueConstraint(
                fields=("drop", "campaign_type"),
                name="unique_drop_email_campaign_type",
            ),
        ),
    ]
