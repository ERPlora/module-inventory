"""Tests for Inventory models."""

import pytest
from decimal import Decimal
from inventory.models import Product, Category


@pytest.mark.django_db
class TestCategory:
    """Tests for Category model."""

    def test_create_category(self):
        """Test creating a category."""
        category = Category.objects.create(
            name='Bebidas',
            icon='cafe-outline',
            color='#FF5722',
            description='Bebidas frías y calientes',
            order=1
        )

        assert category.name == 'Bebidas'
        assert category.icon == 'cafe-outline'
        assert category.color == '#FF5722'
        assert category.is_active is True
        assert category.slug == 'bebidas'

    def test_auto_slug_generation(self):
        """Test slug is auto-generated."""
        category = Category.objects.create(name='Comida Rápida')

        assert category.slug == 'comida-rapida'

    def test_get_initial(self):
        """Test get_initial method."""
        category = Category.objects.create(name='Bebidas')

        assert category.get_initial() == 'B'

    def test_product_count(self):
        """Test product_count property."""
        category = Category.objects.create(name='Test Category')

        # Create active products
        Product.objects.create(
            name='Product 1',
            sku='SKU001',
            price=Decimal('10.00'),
            category=category,
            is_active=True
        )
        Product.objects.create(
            name='Product 2',
            sku='SKU002',
            price=Decimal('15.00'),
            category=category,
            is_active=True
        )

        # Create inactive product (should not count)
        Product.objects.create(
            name='Product 3',
            sku='SKU003',
            price=Decimal('20.00'),
            category=category,
            is_active=False
        )

        assert category.product_count == 2


@pytest.mark.django_db
class TestProduct:
    """Tests for Product model."""

    def test_create_product(self):
        """Test creating a product."""
        category = Category.objects.create(name='Test')

        product = Product.objects.create(
            name='Coca Cola',
            sku='CC-001',
            description='Bebida carbonatada',
            price=Decimal('2.50'),
            cost=Decimal('1.00'),
            stock=100,
            low_stock_threshold=10,
            category=category
        )

        assert product.name == 'Coca Cola'
        assert product.sku == 'CC-001'
        assert product.price == Decimal('2.50')
        assert product.cost == Decimal('1.00')
        assert product.stock == 100
        assert product.is_active is True

    def test_is_low_stock(self):
        """Test is_low_stock property."""
        product = Product.objects.create(
            name='Test Product',
            sku='TST-001',
            price=Decimal('10.00'),
            stock=5,
            low_stock_threshold=10
        )

        assert product.is_low_stock is True

        product.stock = 20
        assert product.is_low_stock is False

    def test_profit_margin(self):
        """Test profit_margin calculation."""
        product = Product.objects.create(
            name='Test Product',
            sku='TST-001',
            price=Decimal('150.00'),
            cost=Decimal('100.00')
        )

        # (150 - 100) / 100 * 100 = 50%
        assert product.profit_margin == 50.0

    def test_profit_margin_zero_cost(self):
        """Test profit_margin with zero cost."""
        product = Product.objects.create(
            name='Free Product',
            sku='FREE-001',
            price=Decimal('10.00'),
            cost=Decimal('0.00')
        )

        assert product.profit_margin == 0

    def test_get_initial(self):
        """Test get_initial method."""
        product = Product.objects.create(
            name='Test Product',
            sku='TST-001',
            price=Decimal('10.00')
        )

        assert product.get_initial() == 'T'

    def test_str_representation(self):
        """Test string representation."""
        product = Product.objects.create(
            name='Test Product',
            sku='TST-001',
            price=Decimal('10.00')
        )

        assert str(product) == 'Test Product (TST-001)'

    def test_unique_sku(self):
        """Test SKU must be unique."""
        Product.objects.create(
            name='Product 1',
            sku='UNIQUE-001',
            price=Decimal('10.00')
        )

        with pytest.raises(Exception):  # IntegrityError
            Product.objects.create(
                name='Product 2',
                sku='UNIQUE-001',  # Duplicate SKU
                price=Decimal('15.00')
            )

    def test_price_validation(self):
        """Test price must be positive."""
        with pytest.raises(Exception):  # ValidationError
            product = Product(
                name='Invalid Product',
                sku='INV-001',
                price=Decimal('-10.00')  # Negative price
            )
            product.full_clean()


# Fixtures
@pytest.fixture
def category():
    """Create test category."""
    return Category.objects.create(
        name='Test Category',
        icon='cube-outline',
        color='#3880ff'
    )


@pytest.fixture
def product(category):
    """Create test product."""
    return Product.objects.create(
        name='Test Product',
        sku='TST-001',
        description='Test Description',
        price=Decimal('10.00'),
        cost=Decimal('5.00'),
        stock=100,
        low_stock_threshold=10,
        category=category
    )
