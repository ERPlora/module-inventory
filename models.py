import os
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class ProductsConfig(models.Model):
    """
    Configuration for Products Plugin.
    Singleton model (only one instance with id=1).
    """
    # Inventory Settings
    allow_negative_stock = models.BooleanField(
        default=False,
        help_text='Allow products to have negative stock values (sell even when out of stock)'
    )

    low_stock_alert_enabled = models.BooleanField(
        default=True,
        help_text='Show alerts when products are low in stock'
    )

    auto_generate_sku = models.BooleanField(
        default=True,
        help_text='Automatically generate SKU for new products'
    )

    barcode_enabled = models.BooleanField(
        default=True,
        help_text='Enable barcode generation and printing for products'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'inventory'
        db_table = 'inventory_config'
        verbose_name = 'Inventory Configuration'
        verbose_name_plural = 'Inventory Configuration'

    def __str__(self):
        return "Products Configuration"

    @classmethod
    def get_config(cls):
        """Get or create products configuration (singleton pattern)"""
        config, _ = cls.objects.get_or_create(id=1)
        return config


class Category(models.Model):
    """
    Modelo de Categoría de Productos
    Definido primero para poder referenciar en Product
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name="Slug")
    icon = models.CharField(
        max_length=50,
        default="cube-outline",
        verbose_name="Icono Ionic",
        help_text="Nombre del icono de Ionicons (ej: cafe-outline, pizza-outline)"
    )
    color = models.CharField(
        max_length=7,
        default="#3880ff",
        verbose_name="Color",
        help_text="Color en formato hexadecimal (ej: #3880ff)"
    )
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        verbose_name="Imagen",
        help_text="Imagen de la categoría (opcional)"
    )
    description = models.TextField(blank=True, verbose_name="Descripción")
    order = models.IntegerField(
        default=0,
        verbose_name="Orden",
        help_text="Orden de visualización (menor número = primero)"
    )
    # Tax Class - default tax for products in this category
    tax_class = models.ForeignKey(
        'configuration.TaxClass',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories',
        verbose_name="Tax Class",
        help_text="Default tax class for products in this category"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        app_label = 'inventory'
        db_table = 'inventory_category'
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-capitaliza el nombre y genera slug si no existe"""
        # Capitalize el nombre automáticamente
        if self.name:
            self.name = self.name.strip().capitalize()

        # Auto-genera slug si no existe
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def product_count(self):
        """Retorna el número de productos en esta categoría"""
        return self.products.filter(is_active=True).count()

    def get_image_url(self):
        """Retorna la URL de la imagen o None"""
        if self.image:
            return self.image.url
        return None

    def get_initial(self):
        """Retorna la primera letra del nombre de la categoría"""
        if self.name:
            # Si el nombre tiene varias palabras, retorna la primera letra de la primera palabra
            return self.name[0].upper()
        return '?'


class Product(models.Model):
    """
    Modelo de Producto
    """
    class ProductType(models.TextChoices):
        PHYSICAL = 'physical', 'Physical Product'
        SERVICE = 'service', 'Service'

    name = models.CharField(max_length=255, verbose_name="Nombre")
    sku = models.CharField(max_length=100, unique=True, verbose_name="SKU")
    ean13 = models.CharField(
        max_length=13,
        blank=True,
        null=True,
        unique=True,
        verbose_name="EAN-13",
        help_text="Código de barras EAN-13 (13 dígitos)"
    )
    description = models.TextField(blank=True, verbose_name="Descripción")

    # Product Type (physical or service)
    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.PHYSICAL,
        verbose_name="Product Type",
        help_text="Physical products affect stock, services do not"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Precio"
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Costo"
    )
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Stock"
    )
    low_stock_threshold = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        verbose_name="Umbral de Stock Bajo"
    )
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='products',
        verbose_name="Categorías",
        help_text="Categorías del producto (puede pertenecer a múltiples)"
    )

    # Tax Class Override (optional, inherits from category if not set)
    tax_class = models.ForeignKey(
        'configuration.TaxClass',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name="Tax Class Override",
        help_text="Override the category's tax class (optional)"
    )

    image = models.ImageField(
        upload_to='products/images/',
        blank=True,
        null=True,
        verbose_name="Imagen"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        app_label = 'inventory'
        db_table = 'inventory_product'
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_low_stock(self):
        """Indica si el producto tiene stock bajo"""
        return self.stock <= self.low_stock_threshold

    @property
    def profit_margin(self):
        """Calcula el margen de ganancia"""
        if self.cost > 0:
            return ((self.price - self.cost) / self.cost) * 100
        return 0

    @property
    def is_service(self):
        """Returns True if this is a service (doesn't affect stock)"""
        return self.product_type == self.ProductType.SERVICE

    def get_effective_tax_class(self):
        """
        Get the effective tax class for this product.
        Inheritance order: Product → Category → StoreConfig.default_tax_class

        Returns:
            TaxClass instance or None
        """
        # 1. Product's own tax_class (override)
        if self.tax_class:
            return self.tax_class

        # 2. First category with tax_class
        for category in self.categories.all():
            if category.tax_class:
                return category.tax_class

        # 3. StoreConfig default_tax_class
        from apps.configuration.models import StoreConfig
        store_config = StoreConfig.get_solo()
        return store_config.default_tax_class

    def get_tax_rate(self):
        """
        Get the effective tax rate for this product.

        Returns:
            Decimal: Tax rate as percentage (e.g., 21.00 for 21%)
        """
        tax_class = self.get_effective_tax_class()
        if tax_class:
            return tax_class.rate

        # Fallback to legacy StoreConfig.tax_rate
        from apps.configuration.models import StoreConfig
        store_config = StoreConfig.get_solo()
        return store_config.tax_rate

    def get_image_path(self):
        """Retorna la ruta relativa de la imagen"""
        if self.image:
            return self.image.url
        return '/static/products/images/placeholder.png'

    def get_initial(self):
        """Retorna la primera letra del nombre del producto"""
        if self.name:
            # Si el nombre tiene varias palabras, retorna la primera letra de la primera palabra
            return self.name[0].upper()
        return '?'

    def save(self, *args, **kwargs):
        """Auto-capitaliza el nombre"""
        if self.name:
            self.name = self.name.strip().capitalize()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Elimina la imagen del filesystem al eliminar el producto"""
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)


class ProductVariant(models.Model):
    """
    Modelo de Variante de Producto
    Permite que un producto tenga múltiples variantes (color, peso, talla, etc.)
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name="Producto"
    )
    name = models.CharField(
        max_length=255,
        verbose_name="Nombre de Variante",
        help_text="Ej: 'Rojo XL', 'Azul M', '1kg', '500ml'"
    )
    sku = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="SKU de Variante",
        help_text="SKU único para esta variante"
    )

    # Atributos de variante (JSON flexible)
    attributes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Atributos",
        help_text="Atributos como {'color': 'rojo', 'talla': 'XL', 'peso': '1kg'}"
    )

    # Precio puede ser diferente para cada variante
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Precio",
        help_text="Precio específico para esta variante (puede ser diferente al producto base)"
    )

    # Stock independiente por variante
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Stock"
    )

    # Imagen específica para la variante (opcional)
    image = models.ImageField(
        upload_to='products/variants/',
        blank=True,
        null=True,
        verbose_name="Imagen de Variante"
    )

    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        app_label = 'inventory'
        db_table = 'inventory_product_variant'
        verbose_name = "Variante de Producto"
        verbose_name_plural = "Variantes de Producto"
        ordering = ['product', 'name']
        unique_together = [['product', 'name']]  # Un producto no puede tener dos variantes con el mismo nombre
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['product', 'is_active']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def save(self, *args, **kwargs):
        """Auto-capitaliza el nombre"""
        if self.name:
            self.name = self.name.strip().capitalize()
        super().save(*args, **kwargs)

    @property
    def is_low_stock(self):
        """Indica si la variante tiene stock bajo (usa el umbral del producto padre)"""
        return self.stock <= self.product.low_stock_threshold

    def delete(self, *args, **kwargs):
        """Elimina la imagen del filesystem al eliminar la variante"""
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)
