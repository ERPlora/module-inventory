"""
End-to-end tests for Inventory module.

Tests complete user flows:
- Browse dashboard → view products → add product → verify it appears
- Create category → assign products → verify counts
- Product lifecycle: create → edit → deactivate → soft-delete
- Export products to CSV
- Settings changes and their effects
"""

import uuid
import pytest
from decimal import Decimal
from django.test import Client
from django.urls import reverse

from inventory.models import Product, Category, InventorySettings

pytestmark = [pytest.mark.e2e, pytest.mark.django_db]

HUB_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')


@pytest.fixture(autouse=True)
def _configure_hub(db, settings):
    """Set up HubConfig + StoreConfig for e2e tests."""
    from apps.configuration.models import HubConfig, StoreConfig
    config = HubConfig.get_solo()
    config.hub_id = HUB_ID
    config.save()
    store = StoreConfig.get_solo()
    store.business_name = 'Test Business'
    store.is_configured = True
    store.save()


@pytest.fixture
def employee(db):
    from apps.accounts.models import LocalUser
    return LocalUser.objects.create(
        name='E2E Employee',
        email='e2e@test.com',
        role='admin',
        is_active=True,
    )


@pytest.fixture
def auth_client(employee):
    client = Client()
    session = client.session
    session['local_user_id'] = str(employee.id)
    session['user_name'] = employee.name
    session['user_email'] = employee.email
    session['user_role'] = employee.role
    session['hub_id'] = str(HUB_ID)
    session['store_config_checked'] = True
    session.save()
    return client


# ---------------------------------------------------------------------------
# Flow: Dashboard → Products → Add Product
# ---------------------------------------------------------------------------

class TestProductCreationFlow:
    """Full flow: visit dashboard → navigate to products → add a product."""

    def test_dashboard_to_product_creation(self, auth_client):
        # 1. Visit dashboard
        response = auth_client.get(reverse('inventory:dashboard'))
        assert response.status_code == 200

        # 2. Navigate to products list
        response = auth_client.get(reverse('inventory:products_list'))
        assert response.status_code == 200

        # 3. Open add product form
        response = auth_client.get(reverse('inventory:product_add'))
        assert response.status_code == 200

        # 4. Create a category first
        cat = Category.objects.create(
            hub_id=HUB_ID, name='Salon Products', icon='cut-outline',
        )

        # 5. Submit new product
        response = auth_client.post(reverse('inventory:product_add'), data={
            'name': 'Professional Shampoo',
            'sku': 'SHP-001',
            'price': '12.99',
            'cost': '5.50',
            'stock': '50',
            'low_stock_threshold': '5',
            'product_type': 'physical',
            'categories': [str(cat.pk)],
        })
        assert response.status_code == 200

        # 6. Verify product was created
        product = Product.objects.get(sku='SHP-001')
        assert product.price == Decimal('12.99')
        assert product.stock == 50
        assert cat in product.categories.all()

        # 7. Verify product shows on products list
        response = auth_client.get(reverse('inventory:products_list'))
        assert response.status_code == 200

    def test_product_creation_validation(self, auth_client):
        """Test that missing required fields show validation error."""
        # Try to create without name/sku/price
        response = auth_client.post(reverse('inventory:product_add'), data={
            'name': '',
            'sku': '',
            'price': '',
        })
        assert response.status_code == 200  # re-renders form
        assert Product.objects.count() == 0


# ---------------------------------------------------------------------------
# Flow: Create Category → Assign Products → Verify Counts
# ---------------------------------------------------------------------------

class TestCategoryProductFlow:
    """Create categories, assign products, verify everything is linked."""

    def test_category_with_products(self, auth_client):
        # 1. Create category via view
        response = auth_client.post(reverse('inventory:category_add'), data={
            'name': 'Hair Care',
            'icon': 'cut-outline',
            'color': '#E91E63',
            'sort_order': '1',
        })
        assert response.status_code == 200
        cat = Category.objects.get(name='Hair care')  # capitalize()

        # 2. Create products and assign to category
        for i in range(3):
            response = auth_client.post(reverse('inventory:product_add'), data={
                'name': f'Product {i}',
                'sku': f'HC-{i:03d}',
                'price': '9.99',
                'stock': str(10 * (i + 1)),
                'product_type': 'physical',
                'categories': [str(cat.pk)],
            })
            assert response.status_code == 200

        # 3. Verify category product count
        assert cat.product_count == 3

        # 4. Verify products list shows all items
        response = auth_client.get(
            reverse('inventory:products_list') + f'?category={cat.pk}'
        )
        assert response.status_code == 200

        # 5. Deactivate one product
        product = Product.objects.filter(sku='HC-000').first()
        response = auth_client.post(
            reverse('inventory:product_toggle_status', args=[product.pk])
        )
        assert response.status_code == 200

        # 6. Active product count should decrease
        assert cat.product_count == 2


# ---------------------------------------------------------------------------
# Flow: Product Lifecycle (create → edit → deactivate → delete)
# ---------------------------------------------------------------------------

class TestProductLifecycle:
    """Full product lifecycle from creation to soft deletion."""

    def test_full_lifecycle(self, auth_client):
        # 1. Create product
        response = auth_client.post(reverse('inventory:product_add'), data={
            'name': 'Temporary Product',
            'sku': 'TMP-001',
            'price': '5.00',
            'stock': '20',
            'product_type': 'physical',
        })
        assert response.status_code == 200
        product = Product.objects.get(sku='TMP-001')
        assert product.is_active is True

        # 2. Edit product
        response = auth_client.post(
            reverse('inventory:product_edit', args=[product.pk]),
            data={
                'name': 'Updated Product',
                'sku': 'TMP-001',
                'price': '7.50',
                'stock': '15',
                'product_type': 'physical',
            },
        )
        assert response.status_code == 200
        product.refresh_from_db()
        assert product.price == Decimal('7.50')

        # 3. Deactivate product
        response = auth_client.post(
            reverse('inventory:product_toggle_status', args=[product.pk])
        )
        assert response.status_code == 200
        product.refresh_from_db()
        assert product.is_active is False

        # 4. Reactivate product
        response = auth_client.post(
            reverse('inventory:product_toggle_status', args=[product.pk])
        )
        assert response.status_code == 200
        product.refresh_from_db()
        assert product.is_active is True

        # 5. Soft-delete product
        response = auth_client.post(
            reverse('inventory:product_delete', args=[product.pk])
        )
        assert response.status_code == 200

        # 6. Product gone from default manager but exists in all_objects
        assert Product.objects.filter(sku='TMP-001').count() == 0
        assert Product.all_objects.filter(sku='TMP-001').count() == 1


# ---------------------------------------------------------------------------
# Flow: Export Products to CSV
# ---------------------------------------------------------------------------

class TestExportFlow:
    """Test exporting data to CSV/Excel."""

    def test_export_products_csv(self, auth_client):
        # 1. Create test data
        for i in range(5):
            Product.objects.create(
                hub_id=HUB_ID,
                name=f'Export Product {i}',
                sku=f'EXP-{i:03d}',
                price=Decimal('10.00'),
                stock=50,
            )

        # 2. Export CSV
        response = auth_client.get(
            reverse('inventory:products_list') + '?export=csv'
        )
        assert response.status_code == 200
        assert 'text/csv' in response['Content-Type']

        # 3. Verify CSV content has rows
        content = response.content.decode('utf-8')
        lines = content.strip().split('\n')
        assert len(lines) >= 6  # header + 5 products

    def test_export_categories_csv(self, auth_client):
        for i in range(3):
            Category.objects.create(
                hub_id=HUB_ID,
                name=f'Category {i}',
                sort_order=i,
            )

        response = auth_client.get(
            reverse('inventory:categories_index') + '?export=csv'
        )
        assert response.status_code == 200
        assert 'text/csv' in response['Content-Type']


# ---------------------------------------------------------------------------
# Flow: Bulk Operations
# ---------------------------------------------------------------------------

class TestBulkOperationsFlow:
    """Test bulk activate/deactivate/delete operations."""

    def test_bulk_deactivate_and_reactivate(self, auth_client):
        # 1. Create products
        ids = []
        for i in range(3):
            p = Product.objects.create(
                hub_id=HUB_ID,
                name=f'Bulk Product {i}',
                sku=f'BLK-{i:03d}',
                price=Decimal('5.00'),
                stock=10,
            )
            ids.append(str(p.pk))

        # 2. Bulk deactivate
        response = auth_client.post(
            reverse('inventory:products_bulk_action'),
            data={'ids': ','.join(ids), 'action': 'deactivate'},
        )
        assert response.status_code == 200

        # 3. Verify all deactivated
        for product_id in ids:
            p = Product.objects.get(pk=product_id)
            assert p.is_active is False

        # 4. Bulk reactivate
        response = auth_client.post(
            reverse('inventory:products_bulk_action'),
            data={'ids': ','.join(ids), 'action': 'activate'},
        )
        assert response.status_code == 200

        for product_id in ids:
            p = Product.objects.get(pk=product_id)
            assert p.is_active is True

    def test_bulk_delete(self, auth_client):
        ids = []
        for i in range(2):
            p = Product.objects.create(
                hub_id=HUB_ID,
                name=f'Del Product {i}',
                sku=f'DEL-{i:03d}',
                price=Decimal('5.00'),
            )
            ids.append(str(p.pk))

        response = auth_client.post(
            reverse('inventory:products_bulk_action'),
            data={'ids': ','.join(ids), 'action': 'delete'},
        )
        assert response.status_code == 200
        assert Product.objects.filter(pk__in=ids).count() == 0


# ---------------------------------------------------------------------------
# Flow: Settings Changes
# ---------------------------------------------------------------------------

class TestSettingsFlow:
    """Test settings changes and their effects."""

    def test_toggle_settings(self, auth_client):
        # 1. Get settings page
        response = auth_client.get(reverse('inventory:settings'))
        assert response.status_code == 200

        # 2. Enable allow_negative_stock
        response = auth_client.post(reverse('inventory:settings'), data={
            'allow_negative_stock': 'on',
            'low_stock_alert_enabled': 'on',
            'auto_generate_sku': 'on',
        })
        assert response.status_code == 200

        # 3. Verify settings were saved
        settings = InventorySettings.get_settings(HUB_ID)
        assert settings.allow_negative_stock is True
        assert settings.low_stock_alert_enabled is True
        assert settings.auto_generate_sku is True

        # 4. Disable some settings
        response = auth_client.post(reverse('inventory:settings'), data={
            'low_stock_alert_enabled': 'on',
        })
        assert response.status_code == 200

        settings = InventorySettings.get_settings(HUB_ID)
        assert settings.allow_negative_stock is False
        assert settings.low_stock_alert_enabled is True


# ---------------------------------------------------------------------------
# Flow: Search and Filter
# ---------------------------------------------------------------------------

class TestSearchFilterFlow:
    """Test searching and filtering products."""

    def test_search_by_name(self, auth_client):
        Product.objects.create(
            hub_id=HUB_ID, name='Shampoo Premium', sku='SHP-P',
            price=Decimal('15.00'), stock=30,
        )
        Product.objects.create(
            hub_id=HUB_ID, name='Conditioner', sku='CND-1',
            price=Decimal('12.00'), stock=20,
        )

        # Search for "Shampoo"
        response = auth_client.get(
            reverse('inventory:products_list') + '?q=Shampoo'
        )
        assert response.status_code == 200

    def test_filter_low_stock(self, auth_client):
        Product.objects.create(
            hub_id=HUB_ID, name='Low Stock Item', sku='LOW-1',
            price=Decimal('5.00'), stock=2, low_stock_threshold=10,
        )
        Product.objects.create(
            hub_id=HUB_ID, name='Normal Item', sku='NRM-1',
            price=Decimal('5.00'), stock=100, low_stock_threshold=10,
        )

        response = auth_client.get(
            reverse('inventory:products_list') + '?status=low_stock'
        )
        assert response.status_code == 200

    def test_sort_by_price(self, auth_client):
        for i, price in enumerate([30, 10, 20]):
            Product.objects.create(
                hub_id=HUB_ID, name=f'Sort Product {i}', sku=f'SRT-{i}',
                price=Decimal(str(price)), stock=10,
            )

        response = auth_client.get(
            reverse('inventory:products_list') + '?sort=price&dir=asc'
        )
        assert response.status_code == 200

        response = auth_client.get(
            reverse('inventory:products_list') + '?sort=price&dir=desc'
        )
        assert response.status_code == 200
