# Generated manually on 2024-11-23

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
from decimal import Decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProductsConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('allow_negative_stock', models.BooleanField(default=False, help_text='Allow products to have negative stock values (sell even when out of stock)')),
                ('low_stock_alert_enabled', models.BooleanField(default=True, help_text='Show alerts when products are low in stock')),
                ('auto_generate_sku', models.BooleanField(default=True, help_text='Automatically generate SKU for new products')),
                ('barcode_enabled', models.BooleanField(default=True, help_text='Enable barcode generation and printing for products')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Inventory Configuration',
                'verbose_name_plural': 'Inventory Configuration',
                'db_table': 'inventory_config',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Nombre')),
                ('slug', models.SlugField(blank=True, max_length=100, unique=True, verbose_name='Slug')),
                ('icon', models.CharField(default='cube-outline', help_text='Nombre del icono de Ionicons (ej: cafe-outline, pizza-outline)', max_length=50, verbose_name='Icono Ionic')),
                ('color', models.CharField(default='#3880ff', help_text='Color en formato hexadecimal (ej: #3880ff)', max_length=7, verbose_name='Color')),
                ('image', models.ImageField(blank=True, help_text='Imagen de la categoría (opcional)', null=True, upload_to='categories/', verbose_name='Imagen')),
                ('description', models.TextField(blank=True, verbose_name='Descripción')),
                ('order', models.IntegerField(default=0, help_text='Orden de visualización (menor número = primero)', verbose_name='Orden')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activa')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Última Actualización')),
            ],
            options={
                'verbose_name': 'Categoría',
                'verbose_name_plural': 'Categorías',
                'db_table': 'inventory_category',
                'ordering': ['order', 'name'],
                'indexes': [
                    models.Index(fields=['order'], name='inventory_c_order_5e8a9c_idx'),
                    models.Index(fields=['is_active'], name='inventory_c_is_acti_a9e7d0_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Nombre')),
                ('sku', models.CharField(max_length=100, unique=True, verbose_name='SKU')),
                ('ean13', models.CharField(blank=True, help_text='Código de barras EAN-13 (13 dígitos)', max_length=13, null=True, unique=True, verbose_name='EAN-13')),
                ('description', models.TextField(blank=True, verbose_name='Descripción')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Precio')),
                ('cost', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Costo')),
                ('stock', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Stock')),
                ('low_stock_threshold', models.IntegerField(default=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Umbral de Stock Bajo')),
                ('image', models.ImageField(blank=True, null=True, upload_to='products/images/', verbose_name='Imagen')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Última Actualización')),
                ('categories', models.ManyToManyField(blank=True, help_text='Categorías del producto (puede pertenecer a múltiples)', related_name='products', to='inventory.category', verbose_name='Categorías')),
            ],
            options={
                'verbose_name': 'Producto',
                'verbose_name_plural': 'Productos',
                'db_table': 'inventory_product',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['sku'], name='inventory_p_sku_3f7b2e_idx'),
                    models.Index(fields=['name'], name='inventory_p_name_8c4f1a_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Ej: 'Rojo XL', 'Azul M', '1kg', '500ml'", max_length=255, verbose_name='Nombre de Variante')),
                ('sku', models.CharField(help_text='SKU único para esta variante', max_length=100, unique=True, verbose_name='SKU de Variante')),
                ('attributes', models.JSONField(blank=True, default=dict, help_text="Atributos como {'color': 'rojo', 'talla': 'XL', 'peso': '1kg'}", verbose_name='Atributos')),
                ('price', models.DecimalField(decimal_places=2, help_text='Precio específico para esta variante (puede ser diferente al producto base)', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Precio')),
                ('stock', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Stock')),
                ('image', models.ImageField(blank=True, null=True, upload_to='products/variants/', verbose_name='Imagen de Variante')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activa')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Última Actualización')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='inventory.product', verbose_name='Producto')),
            ],
            options={
                'verbose_name': 'Variante de Producto',
                'verbose_name_plural': 'Variantes de Producto',
                'db_table': 'inventory_product_variant',
                'ordering': ['product', 'name'],
                'indexes': [
                    models.Index(fields=['sku'], name='inventory_p_sku_variant_7e5d3b_idx'),
                    models.Index(fields=['product', 'is_active'], name='inventory_p_product_active_9a2c4f_idx'),
                ],
            },
        ),
        migrations.AlterUniqueTogether(
            name='productvariant',
            unique_together={('product', 'name')},
        ),
    ]
