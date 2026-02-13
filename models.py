from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.models import HubBaseModel


# --- Settings ---

class InventorySettings(HubBaseModel):
    """Per-hub inventory settings."""

    allow_negative_stock = models.BooleanField(
        _('Allow Negative Stock'),
        default=False,
        help_text=_('Allow products to have negative stock values.'),
    )
    low_stock_alert_enabled = models.BooleanField(
        _('Low Stock Alerts'),
        default=True,
        help_text=_('Show alerts when products are low in stock.'),
    )
    auto_generate_sku = models.BooleanField(
        _('Auto-generate SKU'),
        default=True,
        help_text=_('Automatically generate SKU for new products.'),
    )
    barcode_enabled = models.BooleanField(
        _('Barcode Enabled'),
        default=True,
        help_text=_('Enable barcode generation and printing for products.'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'inventory_settings'
        verbose_name = _('Inventory Settings')
        verbose_name_plural = _('Inventory Settings')
        unique_together = [('hub_id',)]

    def __str__(self):
        return str(_('Inventory Settings'))

    @classmethod
    def get_settings(cls, hub_id):
        """Get or create settings for a hub."""
        settings, _ = cls.all_objects.get_or_create(hub_id=hub_id)
        return settings


# --- Catalogue ---

class Category(HubBaseModel):
    """Product category."""

    name = models.CharField(_('Name'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=100, blank=True)
    icon = models.CharField(
        _('Icon'),
        max_length=50,
        default='cube-outline',
        help_text=_('Icon name (e.g. cafe-outline, pizza-outline)'),
    )
    color = models.CharField(
        _('Color'),
        max_length=7,
        default='#3880ff',
        help_text=_('Hex color (e.g. #3880ff)'),
    )
    image = models.ImageField(
        _('Image'),
        upload_to='categories/',
        blank=True,
        null=True,
    )
    description = models.TextField(_('Description'), blank=True, default='')
    tax_class = models.ForeignKey(
        'configuration.TaxClass',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories',
        verbose_name=_('Tax Class'),
        help_text=_('Default tax class for products in this category.'),
    )
    is_active = models.BooleanField(_('Active'), default=True)
    sort_order = models.PositiveIntegerField(_('Sort Order'), default=0)

    class Meta(HubBaseModel.Meta):
        db_table = 'inventory_category'
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['sort_order']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip().capitalize()
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def product_count(self):
        return self.products.filter(is_deleted=False, is_active=True).count()

    def get_image_url(self):
        if self.image:
            return self.image.url
        return None

    def get_initial(self):
        if self.name:
            return self.name[0].upper()
        return '?'


class Product(HubBaseModel):
    """Product in the catalogue."""

    class ProductType(models.TextChoices):
        PHYSICAL = 'physical', _('Physical Product')
        SERVICE = 'service', _('Service')

    name = models.CharField(_('Name'), max_length=255)
    sku = models.CharField(_('SKU'), max_length=100)
    ean13 = models.CharField(
        _('EAN-13'),
        max_length=13,
        blank=True,
        default='',
        help_text=_('EAN-13 barcode (13 digits).'),
    )
    description = models.TextField(_('Description'), blank=True, default='')
    product_type = models.CharField(
        _('Product Type'),
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.PHYSICAL,
        help_text=_('Physical products affect stock, services do not.'),
    )
    price = models.DecimalField(
        _('Price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    cost = models.DecimalField(
        _('Cost'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    stock = models.IntegerField(_('Stock'), default=0)
    low_stock_threshold = models.PositiveIntegerField(
        _('Low Stock Threshold'),
        default=10,
    )
    categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='products',
        verbose_name=_('Categories'),
    )
    tax_class = models.ForeignKey(
        'configuration.TaxClass',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_('Tax Class Override'),
        help_text=_('Override the category tax class (optional).'),
    )
    image = models.ImageField(
        _('Image'),
        upload_to='products/images/',
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(_('Active'), default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'inventory_product'
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f'{self.name} ({self.sku})'

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip().capitalize()
        super().save(*args, **kwargs)

    @property
    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold

    @property
    def profit_margin(self):
        if self.cost > 0:
            return ((self.price - self.cost) / self.cost) * 100
        return Decimal('0')

    @property
    def is_service(self):
        return self.product_type == self.ProductType.SERVICE

    def get_effective_tax_class(self):
        """
        Tax class inheritance: Product -> Category -> StoreConfig.default_tax_class.
        """
        if self.tax_class:
            return self.tax_class
        for category in self.categories.all():
            if category.tax_class:
                return category.tax_class
        from apps.configuration.models import StoreConfig
        store_config = StoreConfig.get_solo()
        return store_config.default_tax_class

    def get_tax_rate(self):
        """Effective tax rate as percentage (e.g. 21.00)."""
        tax_class = self.get_effective_tax_class()
        if tax_class:
            return tax_class.rate
        from apps.configuration.models import StoreConfig
        store_config = StoreConfig.get_solo()
        return store_config.tax_rate

    def get_image_path(self):
        if self.image:
            return self.image.url
        return '/static/products/images/placeholder.png'

    def get_initial(self):
        if self.name:
            return self.name[0].upper()
        return '?'


class ProductVariant(HubBaseModel):
    """Variant of a product (colour, size, weight, etc.)."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name=_('Product'),
    )
    name = models.CharField(
        _('Variant Name'),
        max_length=255,
        help_text=_("E.g. 'Red XL', 'Blue M', '1kg'"),
    )
    sku = models.CharField(_('Variant SKU'), max_length=100)
    attributes = models.JSONField(
        _('Attributes'),
        default=dict,
        blank=True,
        help_text=_("E.g. {'color': 'red', 'size': 'XL'}"),
    )
    price = models.DecimalField(
        _('Price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    stock = models.IntegerField(_('Stock'), default=0)
    image = models.ImageField(
        _('Variant Image'),
        upload_to='products/variants/',
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(_('Active'), default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'inventory_product_variant'
        verbose_name = _('Product Variant')
        verbose_name_plural = _('Product Variants')
        ordering = ['product', 'name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['product', 'is_active']),
        ]

    def __str__(self):
        return f'{self.product.name} - {self.name}'

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.strip().capitalize()
        super().save(*args, **kwargs)

    @property
    def is_low_stock(self):
        return self.stock <= self.product.low_stock_threshold


# --- Warehousing & Stock ---

class Warehouse(HubBaseModel):
    """Physical or logical warehouse / storage location."""

    name = models.CharField(_('Name'), max_length=100)
    code = models.CharField(
        _('Code'),
        max_length=20,
        blank=True,
        default='',
        help_text=_('Short code (e.g. WH-01).'),
    )
    address = models.TextField(_('Address'), blank=True, default='')
    is_active = models.BooleanField(_('Active'), default=True)
    is_default = models.BooleanField(
        _('Default Warehouse'),
        default=False,
        help_text=_('Default warehouse for new stock.'),
    )
    sort_order = models.PositiveIntegerField(_('Sort Order'), default=0)

    class Meta(HubBaseModel.Meta):
        db_table = 'inventory_warehouse'
        verbose_name = _('Warehouse')
        verbose_name_plural = _('Warehouses')
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class StockLevel(HubBaseModel):
    """Denormalised stock count per product-warehouse pair."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_levels',
        verbose_name=_('Product'),
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='stock_levels',
        verbose_name=_('Warehouse'),
    )
    quantity = models.IntegerField(_('Quantity'), default=0)

    class Meta(HubBaseModel.Meta):
        db_table = 'inventory_stock_level'
        verbose_name = _('Stock Level')
        verbose_name_plural = _('Stock Levels')
        unique_together = [('product', 'warehouse')]

    def __str__(self):
        return f'{self.product.name} @ {self.warehouse.name}: {self.quantity}'


class StockMovement(HubBaseModel):
    """Audit trail for every stock change."""

    class MovementType(models.TextChoices):
        IN = 'in', _('Stock In')
        OUT = 'out', _('Stock Out')
        ADJUSTMENT = 'adjustment', _('Adjustment')
        TRANSFER = 'transfer', _('Transfer')
        RETURN = 'return', _('Return')
        SALE = 'sale', _('Sale')

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_movements',
        verbose_name=_('Product'),
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name=_('Warehouse'),
    )
    movement_type = models.CharField(
        _('Movement Type'),
        max_length=20,
        choices=MovementType.choices,
    )
    quantity = models.IntegerField(
        _('Quantity'),
        help_text=_('Positive for in, negative for out.'),
    )
    reference = models.CharField(
        _('Reference'),
        max_length=100,
        blank=True,
        default='',
        help_text=_('Sale number, PO number, etc.'),
    )
    notes = models.TextField(_('Notes'), blank=True, default='')

    class Meta(HubBaseModel.Meta):
        db_table = 'inventory_stock_movement'
        verbose_name = _('Stock Movement')
        verbose_name_plural = _('Stock Movements')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['movement_type']),
            models.Index(fields=['product', 'warehouse']),
        ]

    def __str__(self):
        return f'{self.get_movement_type_display()} {self.quantity} x {self.product.name}'


class StockAlert(HubBaseModel):
    """Alert when a product falls below its low-stock threshold."""

    class AlertStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        ACKNOWLEDGED = 'acknowledged', _('Acknowledged')
        RESOLVED = 'resolved', _('Resolved')

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_alerts',
        verbose_name=_('Product'),
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_alerts',
        verbose_name=_('Warehouse'),
    )
    current_stock = models.IntegerField(_('Current Stock'))
    threshold = models.IntegerField(_('Threshold'))
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=AlertStatus.choices,
        default=AlertStatus.ACTIVE,
    )
    acknowledged_at = models.DateTimeField(_('Acknowledged At'), null=True, blank=True)
    resolved_at = models.DateTimeField(_('Resolved At'), null=True, blank=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'inventory_stock_alert'
        verbose_name = _('Stock Alert')
        verbose_name_plural = _('Stock Alerts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'Alert: {self.product.name} ({self.current_stock}/{self.threshold})'
