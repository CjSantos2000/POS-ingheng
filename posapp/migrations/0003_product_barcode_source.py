from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posapp", "0002_product_category_choices"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="barcode_source",
            field=models.CharField(
                choices=[("manual", "Manual"), ("generated", "Generated")],
                default="manual",
                max_length=20,
            ),
        ),
    ]