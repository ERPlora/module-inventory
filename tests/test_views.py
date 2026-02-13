"""
Integration tests for Inventory views.
"""

import uuid
import pytest
from decimal import Decimal
from django.test import Client
from django.urls import reverse

from inventory.models import Product, Category, InventorySettings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

HUB_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')


@pytest.fixture(autouse=True)
def _set_hub_config(db, settings):
    """Ensure HubConfig + StoreConfig exist so setup middleware won't redirect."""
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
    """Create a local user (employee)."""
    from apps.accounts.models import LocalUser
    return LocalUser.objects.create(
        name='Test Employee',
        email='employee@test.com',
        role='admin',
        is_active=True,
    )


@pytest.fixture
def auth_client(employee):
    """Authenticated Django test client."""
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


@pytest.fixture
def category():
    """Create a test category."""
    return Category.objects.create(
        hub_id=HUB_ID,
        name='Bebidas',
        icon='cafe-outline',
        color='#FF5722',
    )


@pytest.fixture
def product(category):
    """Create a test product with a category."""
    p = Product.objects.create(
        hub_id=HUB_ID,
        name='Coca Cola',
        sku='CC-001',
        price=Decimal('2.50'),
        cost=Decimal('1.00'),
        stock=100,
        low_stock_threshold=10,
    )
    p.categories.add(category)
    return p


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDashboard:

    def test_requires_login(self):
        client = Client()
        response = client.get(reverse('inventory:dashboard'))
        assert response.status_code == 302

    def test_authenticated(self, auth_client):
        response = auth_client.get(reverse('inventory:dashboard'))
        assert response.status_code == 200

    def test_htmx_returns_partial(self, auth_client):
        response = auth_client.get(
            reverse('inventory:dashboard'), HTTP_HX_REQUEST='true'
        )
        assert response.status_code == 200

    def test_dashboard_with_products(self, auth_client, product):
        response = auth_client.get(reverse('inventory:dashboard'))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Products — List
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProductsList:

    def test_get(self, auth_client, product):
        response = auth_client.get(reverse('inventory:products_list'))
        assert response.status_code == 200

    def test_search(self, auth_client, product):
        response = auth_client.get(
            reverse('inventory:products_list') + '?q=Coca'
        )
        assert response.status_code == 200

    def test_filter_by_category(self, auth_client, product, category):
        response = auth_client.get(
            reverse('inventory:products_list') + f'?category={category.pk}'
        )
        assert response.status_code == 200

    def test_filter_by_status(self, auth_client, product):
        response = auth_client.get(
            reverse('inventory:products_list') + '?status=active'
        )
        assert response.status_code == 200

    def test_sort(self, auth_client, product):
        response = auth_client.get(
            reverse('inventory:products_list') + '?sort=price&dir=desc'
        )
        assert response.status_code == 200

    def test_export_csv(self, auth_client, product):
        response = auth_client.get(
            reverse('inventory:products_list') + '?export=csv'
        )
        assert response.status_code == 200
        assert 'text/csv' in response['Content-Type']

    def test_export_excel(self, auth_client, product):
        response = auth_client.get(
            reverse('inventory:products_list') + '?export=excel'
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Products — CRUD
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestProductCRUD:

    def test_add_get(self, auth_client):
        response = auth_client.get(reverse('inventory:product_add'))
        assert response.status_code == 200

    def test_add_post(self, auth_client, category):
        response = auth_client.post(
            reverse('inventory:product_add'),
            data={
                'name': 'Fanta',
                'sku': 'FAN-001',
                'price': '1.80',
                'cost': '0.50',
                'stock': '50',
                'low_stock_threshold': '5',
                'product_type': 'physical',
                'categories': [str(category.pk)],
            },
        )
        assert response.status_code == 200
        assert Product.objects.filter(sku='FAN-001').exists()

    def test_add_missing_fields(self, auth_client):
        response = auth_client.post(
            reverse('inventory:product_add'),
            data={'name': '', 'sku': '', 'price': ''},
        )
        assert response.status_code == 200  # renders form with error

    def test_edit_get(self, auth_client, product):
        response = auth_client.get(
            reverse('inventory:product_edit', args=[product.pk])
        )
        assert response.status_code == 200

    def test_edit_post(self, auth_client, product):
        response = auth_client.post(
            reverse('inventory:product_edit', args=[product.pk]),
            data={
                'name': 'Coca Cola Zero',
                'sku': 'CC-001',
                'price': '2.80',
                'cost': '1.20',
                'stock': '80',
                'low_stock_threshold': '10',
                'product_type': 'physical',
            },
        )
        assert response.status_code == 200
        product.refresh_from_db()
        assert product.price == Decimal('2.80')

    def test_delete(self, auth_client, product):
        response = auth_client.post(
            reverse('inventory:product_delete', args=[product.pk])
        )
        assert response.status_code == 200
        # soft delete — not in default manager
        assert Product.objects.filter(pk=product.pk).count() == 0
        assert Product.all_objects.filter(pk=product.pk).count() == 1

    def test_toggle_status(self, auth_client, product):
        assert product.is_active is True
        response = auth_client.post(
            reverse('inventory:product_toggle_status', args=[product.pk])
        )
        assert response.status_code == 200
        product.refresh_from_db()
        assert product.is_active is False

    def test_bulk_deactivate(self, auth_client, product):
        response = auth_client.post(
            reverse('inventory:products_bulk_action'),
            data={'ids': str(product.pk), 'action': 'deactivate'},
        )
        assert response.status_code == 200
        product.refresh_from_db()
        assert product.is_active is False

    def test_bulk_delete(self, auth_client, product):
        response = auth_client.post(
            reverse('inventory:products_bulk_action'),
            data={'ids': str(product.pk), 'action': 'delete'},
        )
        assert response.status_code == 200
        assert Product.objects.filter(pk=product.pk).count() == 0


# ---------------------------------------------------------------------------
# Categories — List
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCategoriesList:

    def test_get(self, auth_client, category):
        response = auth_client.get(reverse('inventory:categories_index'))
        assert response.status_code == 200

    def test_search(self, auth_client, category):
        response = auth_client.get(
            reverse('inventory:categories_index') + '?q=Bebidas'
        )
        assert response.status_code == 200

    def test_export_csv(self, auth_client, category):
        response = auth_client.get(
            reverse('inventory:categories_index') + '?export=csv'
        )
        assert response.status_code == 200
        assert 'text/csv' in response['Content-Type']


# ---------------------------------------------------------------------------
# Categories — CRUD
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCategoryCRUD:

    def test_add_get(self, auth_client):
        response = auth_client.get(reverse('inventory:category_add'))
        assert response.status_code == 200

    def test_add_post(self, auth_client):
        response = auth_client.post(
            reverse('inventory:category_add'),
            data={
                'name': 'Comida Rapida',
                'icon': 'pizza-outline',
                'color': '#FF9800',
                'sort_order': '1',
            },
        )
        assert response.status_code == 200
        assert Category.objects.filter(name='Comida rapida').exists()

    def test_add_missing_name(self, auth_client):
        response = auth_client.post(
            reverse('inventory:category_add'),
            data={'name': ''},
        )
        assert response.status_code == 200  # renders form with error

    def test_edit_post(self, auth_client, category):
        response = auth_client.post(
            reverse('inventory:category_edit', args=[category.pk]),
            data={
                'name': 'Refrescos',
                'icon': 'beer-outline',
                'color': '#00BCD4',
                'sort_order': '2',
            },
        )
        assert response.status_code == 200
        category.refresh_from_db()
        assert category.name == 'Refrescos'

    def test_delete(self, auth_client, category):
        response = auth_client.post(
            reverse('inventory:category_delete', args=[category.pk])
        )
        assert response.status_code == 200
        assert Category.objects.filter(pk=category.pk).count() == 0

    def test_toggle_status(self, auth_client, category):
        response = auth_client.post(
            reverse('inventory:category_toggle_status', args=[category.pk])
        )
        assert response.status_code == 200
        category.refresh_from_db()
        assert category.is_active is False

    def test_bulk_delete(self, auth_client, category):
        response = auth_client.post(
            reverse('inventory:categories_bulk_action'),
            data={'ids': str(category.pk), 'action': 'delete'},
        )
        assert response.status_code == 200
        assert Category.objects.filter(pk=category.pk).count() == 0


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSettingsView:

    def test_get(self, auth_client):
        response = auth_client.get(reverse('inventory:settings'))
        assert response.status_code == 200

    def test_save(self, auth_client):
        response = auth_client.post(
            reverse('inventory:settings'),
            data={
                'allow_negative_stock': 'on',
                'low_stock_alert_enabled': 'on',
            },
        )
        assert response.status_code == 200
        settings = InventorySettings.get_settings(HUB_ID)
        assert settings.allow_negative_stock is True
        assert settings.low_stock_alert_enabled is True


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestReports:

    def test_reports_page(self, auth_client):
        response = auth_client.get(reverse('inventory:reports'))
        assert response.status_code == 200

    def test_reports_with_data(self, auth_client, product):
        response = auth_client.get(reverse('inventory:reports'))
        assert response.status_code == 200
