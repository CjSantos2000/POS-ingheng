# Generated migration for Product category choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(
                blank=True,
                choices=[
                    ('notebook', 'Notebooks'),
                    ('pen', 'Pens & Pencils'),
                    ('paper', 'Paper Products'),
                    ('snack', 'Snacks & Beverages'),
                    ('supplies', 'School Supplies'),
                    ('other', 'Other'),
                ],
                default='other',
                max_length=120
            ),
        ),
    ]
