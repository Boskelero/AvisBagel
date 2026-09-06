from django.db import migrations


def seed_tiers(apps, schema_editor):
    BagelPriceTier = apps.get_model("drops", "BagelPriceTier")
    for quantity, price_cents in [(1, 1200), (6, 6500), (12, 12000)]:
        BagelPriceTier.objects.update_or_create(
            quantity=quantity,
            defaults={"price_cents": price_cents, "is_active": True},
        )


class Migration(migrations.Migration):
    dependencies = [("drops", "0001_initial")]
    operations = [migrations.RunPython(seed_tiers, migrations.RunPython.noop)]
