# Generated migration with data migration for slugs and category conversion
import django.db.models.deletion
from django.db import migrations, models
from django.utils.text import slugify


def generate_slugs(apps, schema_editor):
    """Generate slugs for existing categories"""
    Category = apps.get_model('inventory', 'Category')
    for category in Category.objects.all():
        if not category.slug:
            base_slug = slugify(category.name)
            slug = base_slug
            counter = 1
            # Ensure uniqueness
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            category.slug = slug
            category.save()


def migrate_product_categories(apps, schema_editor):
    """Convert product categories from string to ForeignKey"""
    Product = apps.get_model('inventory', 'Product')
    Category = apps.get_model('inventory', 'Category')

    # Build a map of category names to IDs
    category_map = {cat.name: cat.id for cat in Category.objects.all()}

    # Create a "General" category if it doesn't exist
    if 'General' not in category_map:
        general_category = Category.objects.create(
            name='General',
            icon='cube-outline',
            slug='general',
            is_active=True,
            order=999
        )
        category_map['General'] = general_category.id

    # Map each product's string category to Category ID
    for product in Product.objects.all():
        if product.category_old and product.category_old in category_map:
            # Use existing category
            product.category_id = category_map[product.category_old]
        elif product.category_old:
            # Category name exists but not in our map - try to create it with unique slug
            base_slug = slugify(product.category_old)
            slug = base_slug
            counter = 1
            # Ensure unique slug
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            category = Category.objects.create(
                name=product.category_old,
                icon='cube-outline',
                slug=slug,
                is_active=True
            )
            category_map[product.category_old] = category.id
            product.category_id = category.id
        else:
            # No category, assign to General
            product.category_id = category_map.get('General')

        product.save()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        # Step 1: Add new fields to Category without unique constraint on slug
        migrations.AddField(
            model_name='category',
            name='color',
            field=models.CharField(
                default='#3880ff',
                help_text='Color en formato hexadecimal (ej: #3880ff)',
                max_length=7,
                verbose_name='Color'
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='order',
            field=models.IntegerField(
                default=0,
                help_text='Orden de visualización (menor número = primero)',
                verbose_name='Orden'
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='slug',
            field=models.SlugField(
                blank=True,
                max_length=100,
                verbose_name='Slug'
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True,
                verbose_name='Última Actualización'
            ),
        ),

        # Step 2: Generate slugs for existing categories
        migrations.RunPython(generate_slugs, migrations.RunPython.noop),

        # Step 3: Now make slug unique
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(
                max_length=100,
                unique=True,
                verbose_name='Slug'
            ),
        ),

        # Step 4: Update Category icon field
        migrations.AlterField(
            model_name='category',
            name='icon',
            field=models.CharField(
                default='cube-outline',
                help_text='Nombre del icono de Ionicons (ej: cafe-outline, pizza-outline)',
                max_length=50,
                verbose_name='Icono Ionic'
            ),
        ),

        # Step 5: Remove index on category field before renaming
        migrations.RemoveIndex(
            model_name='product',
            name='products_pr_categor_14b9c0_idx',
        ),

        # Step 6: Rename old category field on Product
        migrations.RenameField(
            model_name='product',
            old_name='category',
            new_name='category_old',
        ),

        # Step 7: Add new ForeignKey field (nullable)
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(
                blank=True,
                help_text="Categoría del producto. Si no se especifica, se asigna 'General'",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='products',
                to='inventory.category',
                verbose_name='Categoría'
            ),
        ),

        # Step 8: Migrate data from category_old to category FK
        migrations.RunPython(migrate_product_categories, migrations.RunPython.noop),

        # Step 9: Remove old category_old field
        migrations.RemoveField(
            model_name='product',
            name='category_old',
        ),

        # Step 10: Update Category Meta
        migrations.AlterModelOptions(
            name='category',
            options={
                'ordering': ['order', 'name'],
                'verbose_name': 'Categoría',
                'verbose_name_plural': 'Categorías'
            },
        ),

        # Step 11: Add indexes
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['order'], name='products_ca_order_ac6215_idx'),
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['is_active'], name='products_ca_is_acti_a2d000_idx'),
        ),

        # Step 12: Add index for new category FK
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['category'], name='products_pr_categor_9edb3d_idx'),
        ),
    ]
