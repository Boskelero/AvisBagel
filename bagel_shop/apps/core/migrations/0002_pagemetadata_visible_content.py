from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]

    operations = [
        migrations.AddField(model_name="pagemetadata", name="heading_en", field=models.CharField(blank=True, max_length=200)),
        migrations.AddField(model_name="pagemetadata", name="heading_he", field=models.CharField(blank=True, max_length=200)),
        migrations.AddField(model_name="pagemetadata", name="intro_en", field=models.TextField(blank=True)),
        migrations.AddField(model_name="pagemetadata", name="intro_he", field=models.TextField(blank=True)),
        migrations.AddField(model_name="pagemetadata", name="content_en", field=models.TextField(blank=True)),
        migrations.AddField(model_name="pagemetadata", name="content_he", field=models.TextField(blank=True)),
    ]
