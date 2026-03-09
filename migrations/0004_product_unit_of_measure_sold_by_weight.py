from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_category_code_product_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='unit_of_measure',
            field=models.CharField(
                choices=[
                    ('unit', 'Unit'),
                    ('kg', 'Kilogram'),
                    ('g', 'Gram'),
                    ('l', 'Litre'),
                    ('ml', 'Millilitre'),
                    ('m', 'Metre'),
                    ('cm', 'Centimetre'),
                ],
                default='unit',
                help_text='How this product is measured and sold.',
                max_length=10,
                verbose_name='Unit of Measure',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='sold_by_weight',
            field=models.BooleanField(
                default=False,
                help_text='Requires entering weight/quantity at the POS before adding to cart.',
                verbose_name='Sold by Weight/Measure',
            ),
        ),
    ]
