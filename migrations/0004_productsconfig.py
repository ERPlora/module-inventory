# Generated manually on 2025-01-15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_category_image_alter_category_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductsConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('allow_negative_stock', models.BooleanField(default=False, help_text='Allow products to have negative stock values (sell even when out of stock)')),
                ('low_stock_alert_enabled', models.BooleanField(default=True, help_text='Show alerts when products are low in stock')),
                ('auto_generate_sku', models.BooleanField(default=True, help_text='Automatically generate SKU for new products')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Products Configuration',
                'verbose_name_plural': 'Products Configuration',
                'db_table': 'products_config',
            },
        ),
    ]
