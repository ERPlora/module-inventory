"""Tests for Products views."""

import pytest
from decimal import Decimal
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Product, Category


User = get_user_model()


@pytest.fixture
def user(db):
    """Create test user."""
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def authenticated_client(user):
    """Create authenticated client."""
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def category(db):
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
        price=Decimal('10.00'),
        cost=Decimal('5.00'),
        stock=100,
        category=category
    )


@pytest.mark.django_db
class TestProductViews:
    """Tests for product views."""

    def test_index_requires_login(self):
        """Test index view requires authentication."""
        client = Client()
        response = client.get(reverse('products:index'))

        assert response.status_code == 302  # Redirect to login

    def test_index_authenticated(self, authenticated_client):
        """Test index view with authentication."""
        response = authenticated_client.get(reverse('products:index'))

        assert response.status_code == 200
        assert 'total_products' in response.context

    def test_product_list_ajax(self, authenticated_client, product):
        """Test product list AJAX endpoint."""
        response = authenticated_client.get(reverse('products:product_list_ajax'))

        assert response.status_code == 200
        data = response.json()
        assert 'products' in data
        assert len(data['products']) == 1

    def test_product_create_get(self, authenticated_client):
        """Test GET product create view."""
        response = authenticated_client.get(reverse('products:product_create'))

        assert response.status_code == 200

    def test_product_create_post(self, authenticated_client, category):
        """Test POST product create."""
        data = {
            'name': 'New Product',
            'sku': 'NEW-001',
            'price': '19.99',
            'cost': '10.00',
            'stock': '50',
            'category_id': category.id
        }

        response = authenticated_client.post(reverse('products:product_create'), data)

        assert response.status_code == 200
        assert Product.objects.filter(sku='NEW-001').exists()

    def test_product_edit(self, authenticated_client, product):
        """Test product edit."""
        data = {
            'name': 'Updated Product',
            'sku': product.sku,
            'price': '25.00',
            'cost': '15.00',
            'stock': '200',
            'category_id': product.category.id
        }

        response = authenticated_client.post(
            reverse('products:product_edit', args=[product.pk]),
            data
        )

        assert response.status_code == 200
        product.refresh_from_db()
        assert product.name == 'Updated Product'
        assert product.price == Decimal('25.00')

    def test_product_delete(self, authenticated_client, product):
        """Test product delete."""
        product_id = product.pk

        response = authenticated_client.post(
            reverse('products:product_delete', args=[product_id])
        )

        assert response.status_code == 200
        assert not Product.objects.filter(pk=product_id).exists()

    def test_export_csv(self, authenticated_client, product):
        """Test CSV export."""
        response = authenticated_client.get(reverse('products:export_csv'))

        assert response.status_code == 200
        assert response['Content-Type'] == 'text/csv; charset=utf-8'
        assert 'productos.csv' in response['Content-Disposition']


@pytest.mark.django_db
class TestCategoryViews:
    """Tests for category views."""

    def test_categories_index(self, authenticated_client, category):
        """Test categories index view."""
        response = authenticated_client.get(reverse('products:categories_index'))

        assert response.status_code == 200
        assert 'categories' in response.context
        assert response.context['total_categories'] == 1

    def test_category_create(self, authenticated_client):
        """Test category create."""
        data = {
            'name': 'New Category',
            'icon': 'pizza-outline',
            'color': '#FF5722',
            'order': '1'
        }

        response = authenticated_client.post(
            reverse('products:category_create'),
            data
        )

        assert response.status_code == 200
        assert Category.objects.filter(name='New Category').exists()

    def test_category_edit(self, authenticated_client, category):
        """Test category edit."""
        data = {
            'name': 'Updated Category',
            'icon': 'cafe-outline',
            'color': '#00FF00',
            'order': '5'
        }

        response = authenticated_client.post(
            reverse('products:category_edit', args=[category.pk]),
            data
        )

        assert response.status_code == 200
        category.refresh_from_db()
        assert category.name == 'Updated Category'

    def test_category_delete_with_products(self, authenticated_client, category, product):
        """Test cannot delete category with products."""
        response = authenticated_client.post(
            reverse('products:category_delete', args=[category.pk])
        )

        data = response.json()
        assert response.status_code == 400
        assert 'productos asociados' in data['message']

    def test_category_delete_empty(self, authenticated_client, category):
        """Test delete category without products."""
        response = authenticated_client.post(
            reverse('products:category_delete', args=[category.pk])
        )

        assert response.status_code == 200
        assert not Category.objects.filter(pk=category.pk).exists()

    def test_categories_list_api(self, authenticated_client, category):
        """Test categories list API."""
        response = authenticated_client.get(reverse('products:categories_list'))

        assert response.status_code == 200
        data = response.json()
        assert 'categories' in data
        assert len(data['categories']) == 1
        assert data['categories'][0]['name'] == category.name
