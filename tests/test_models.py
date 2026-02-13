"""Tests for Inventory models."""

import uuid
import pytest
from decimal import Decimal
from inventory.models import (
    InventorySettings, Category, Product, ProductVariant,
    Warehouse, StockLevel, StockMovement, StockAlert,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def hub_id():
    return uuid.uuid4()


@pytest.fixture
def category(hub_id):
    return Category.objects.create(
        hub_id=hub_id,
        name='Bebidas',
        icon='cafe-outline',
        color='#FF5722',
        description='Bebidas frias y calientes',
    )


@pytest.fixture
def product(hub_id, category):
    p = Product.objects.create(
        hub_id=hub_id,
        name='Coca Cola',
        sku='CC-001',
        description='Bebida carbonatada',
        price=Decimal('2.50'),
        cost=Decimal('1.00'),
        stock=100,
        low_stock_threshold=10,
    )
    p.categories.add(category)
    return p


# ---------------------------------------------------------------------------
# InventorySettings
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestInventorySettings:

    def test_get_settings_creates(self, hub_id):
        s = InventorySettings.get_settings(hub_id)
        assert s is not None
        assert s.hub_id == hub_id

    def test_get_settings_returns_existing(self, hub_id):
        s1 = InventorySettings.get_settings(hub_id)
        s2 = InventorySettings.get_settings(hub_id)
        assert s1.pk == s2.pk

    def test_defaults(self, hub_id):
        s = InventorySettings.get_settings(hub_id)
        assert s.allow_negative_stock is False
        assert s.low_stock_alert_enabled is True
        assert s.auto_generate_sku is True
        assert s.barcode_enabled is True

    def test_str(self, hub_id):
        s = InventorySettings.get_settings(hub_id)
        result = str(s)
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCategory:

    def test_create(self, category):
        assert category.name == 'Bebidas'
        assert category.icon == 'cafe-outline'
        assert category.color == '#FF5722'
        assert category.is_active is True

    def test_auto_slug(self):
        cat = Category.objects.create(name='Comida Rapida')
        assert cat.slug == 'comida-rapida'

    def test_name_capitalized(self):
        cat = Category.objects.create(name='test category')
        assert cat.name == 'Test category'

    def test_get_initial(self, category):
        assert category.get_initial() == 'B'

    def test_product_count(self, category, product):
        assert category.product_count == 1

    def test_product_count_excludes_inactive(self, hub_id, category):
        p = Product.objects.create(
            hub_id=hub_id, name='Inactive', sku='INA-001',
            price=Decimal('5.00'), is_active=False,
        )
        p.categories.add(category)
        assert category.product_count == 0

    def test_product_count_excludes_deleted(self, hub_id, category):
        p = Product.objects.create(
            hub_id=hub_id, name='Deleted', sku='DEL-001',
            price=Decimal('5.00'),
        )
        p.categories.add(category)
        p.delete()  # soft delete
        assert category.product_count == 0

    def test_str(self, category):
        assert str(category) == 'Bebidas'

    def test_ordering(self, hub_id):
        c1 = Category.objects.create(hub_id=hub_id, name='Z', sort_order=2)
        c2 = Category.objects.create(hub_id=hub_id, name='A', sort_order=1)
        cats = list(Category.objects.filter(hub_id=hub_id))
        assert cats[0].pk == c2.pk

    def test_soft_delete(self, category):
        category.delete()
        assert category.is_deleted is True
        assert Category.objects.filter(pk=category.pk).count() == 0
        assert Category.all_objects.filter(pk=category.pk).count() == 1


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProduct:

    def test_create(self, product):
        assert product.name == 'Coca cola'  # capitalize()
        assert product.sku == 'CC-001'
        assert product.price == Decimal('2.50')
        assert product.cost == Decimal('1.00')
        assert product.stock == 100
        assert product.is_active is True

    def test_is_low_stock_true(self):
        p = Product.objects.create(
            name='Low', sku='LOW-001', price=Decimal('10.00'),
            stock=5, low_stock_threshold=10,
        )
        assert p.is_low_stock is True

    def test_is_low_stock_false(self):
        p = Product.objects.create(
            name='High', sku='HIGH-001', price=Decimal('10.00'),
            stock=20, low_stock_threshold=10,
        )
        assert p.is_low_stock is False

    def test_profit_margin(self, product):
        # (2.50 - 1.00) / 1.00 * 100 = 150%
        assert product.profit_margin == 150.0

    def test_profit_margin_zero_cost(self):
        p = Product.objects.create(
            name='Free', sku='FREE-001', price=Decimal('10.00'),
            cost=Decimal('0.00'),
        )
        assert p.profit_margin == 0

    def test_is_service(self):
        p = Product.objects.create(
            name='Service', sku='SVC-001', price=Decimal('25.00'),
            product_type='service',
        )
        assert p.is_service is True

    def test_is_not_service(self, product):
        assert product.is_service is False

    def test_get_initial(self, product):
        assert product.get_initial() == 'C'

    def test_str(self, product):
        assert 'CC-001' in str(product)

    def test_default_product_type(self, product):
        assert product.product_type == 'physical'

    def test_m2m_categories(self, product, category):
        assert category in product.categories.all()

    def test_soft_delete(self, product):
        product.delete()
        assert product.is_deleted is True
        assert Product.objects.filter(pk=product.pk).count() == 0


# ---------------------------------------------------------------------------
# ProductVariant
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProductVariant:

    def test_create(self, hub_id, product):
        v = ProductVariant.objects.create(
            hub_id=hub_id, product=product,
            name='Red XL', sku='CC-001-RXL',
            price=Decimal('3.00'), stock=50,
            attributes={'color': 'red', 'size': 'XL'},
        )
        assert v.name == 'Red xl'  # capitalize()
        assert v.attributes['color'] == 'red'

    def test_is_low_stock(self, hub_id, product):
        v = ProductVariant.objects.create(
            hub_id=hub_id, product=product,
            name='Small', sku='CC-S', price=Decimal('2.00'),
            stock=5,
        )
        assert v.is_low_stock is True  # product.low_stock_threshold=10

    def test_str(self, hub_id, product):
        v = ProductVariant.objects.create(
            hub_id=hub_id, product=product,
            name='Blue', sku='CC-B', price=Decimal('2.50'),
        )
        assert product.name in str(v)


# ---------------------------------------------------------------------------
# Warehouse & Stock
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestWarehouse:

    def test_create(self, hub_id):
        wh = Warehouse.objects.create(
            hub_id=hub_id, name='Main', code='WH-01',
            is_default=True,
        )
        assert wh.name == 'Main'
        assert wh.is_default is True

    def test_str(self, hub_id):
        wh = Warehouse.objects.create(hub_id=hub_id, name='Storage')
        assert str(wh) == 'Storage'


@pytest.mark.django_db
class TestStockLevel:

    def test_create(self, hub_id, product):
        wh = Warehouse.objects.create(hub_id=hub_id, name='WH1')
        sl = StockLevel.objects.create(
            hub_id=hub_id, product=product, warehouse=wh,
            quantity=50,
        )
        assert sl.quantity == 50

    def test_str(self, hub_id, product):
        wh = Warehouse.objects.create(hub_id=hub_id, name='WH1')
        sl = StockLevel.objects.create(
            hub_id=hub_id, product=product, warehouse=wh,
            quantity=25,
        )
        assert '25' in str(sl)


@pytest.mark.django_db
class TestStockMovement:

    def test_create(self, hub_id, product):
        wh = Warehouse.objects.create(hub_id=hub_id, name='WH1')
        sm = StockMovement.objects.create(
            hub_id=hub_id, product=product, warehouse=wh,
            movement_type='in', quantity=100,
            reference='PO-001', notes='Initial stock',
        )
        assert sm.movement_type == 'in'
        assert sm.quantity == 100

    def test_all_movement_types(self, hub_id, product):
        for mt, _ in StockMovement.MovementType.choices:
            sm = StockMovement.objects.create(
                hub_id=hub_id, product=product,
                movement_type=mt, quantity=1,
            )
            assert sm.movement_type == mt

    def test_str(self, hub_id, product):
        sm = StockMovement.objects.create(
            hub_id=hub_id, product=product,
            movement_type='sale', quantity=-2,
        )
        assert product.name in str(sm)


@pytest.mark.django_db
class TestStockAlert:

    def test_create(self, hub_id, product):
        alert = StockAlert.objects.create(
            hub_id=hub_id, product=product,
            current_stock=3, threshold=10,
        )
        assert alert.status == 'active'

    def test_str(self, hub_id, product):
        alert = StockAlert.objects.create(
            hub_id=hub_id, product=product,
            current_stock=3, threshold=10,
        )
        assert product.name in str(alert)
        assert '3' in str(alert)
