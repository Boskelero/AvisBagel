from django.db import migrations
from django.db.models import F


def sync_bagel_product_prices(apps, schema_editor):
    BagelPriceTier = apps.get_model("drops", "BagelPriceTier")
    Product = apps.get_model("catalog", "Product")
    single_price_cents = (
        BagelPriceTier.objects.filter(quantity=1, is_active=True)
        .values_list("price_cents", flat=True)
        .first()
    )
    if single_price_cents is not None:
        Product.objects.filter(product_type="bagel").update(
            price_cents=single_price_cents + F("specialty_upcharge_cents")
        )


class Migration(migrations.Migration):
    dependencies = [("drops", "0002_seed_bagel_price_tiers")]
    operations = [
        migrations.RunPython(sync_bagel_product_prices, migrations.RunPython.noop),
    ]
