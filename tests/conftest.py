"""
Pytest configuration for inventory module tests.

This conftest ensures Django is properly configured when running tests
from within the module directory.
"""
import os
import sys
from pathlib import Path

# Ensure Django settings are configured before any imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Add the hub directory to Python path
HUB_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'hub'
if str(HUB_DIR) not in sys.path:
    sys.path.insert(0, str(HUB_DIR))

# Add the modules directory to Python path
MODULES_DIR = Path(__file__).resolve().parent.parent.parent
if str(MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(MODULES_DIR))

# Now setup Django
import django
django.setup()

# Disable debug toolbar during tests to avoid namespace errors
from django.conf import settings
if 'debug_toolbar' in settings.INSTALLED_APPS:
    settings.INSTALLED_APPS = [
        app for app in settings.INSTALLED_APPS if app != 'debug_toolbar'
    ]
if hasattr(settings, 'MIDDLEWARE'):
    settings.MIDDLEWARE = [
        m for m in settings.MIDDLEWARE if 'debug_toolbar' not in m
    ]

# Import pytest and fixtures
import pytest
from decimal import Decimal
from django.test import Client

from apps.accounts.models import LocalUser


@pytest.fixture
def client():
    """Create test client."""
    return Client()


@pytest.fixture
def user(db):
    """Create a test user."""
    from django.contrib.auth.hashers import make_password
    return LocalUser.objects.create(
        name="Test User",
        email="testuser@example.com",
        pin_hash=make_password("1234"),
        is_active=True
    )


@pytest.fixture
def hub_config(db):
    """Create required HubConfig for tests (required by setup middleware)."""
    from apps.configuration.models import HubConfig
    config, _ = HubConfig.objects.get_or_create(id=1, defaults={
        'is_configured': True,
        'currency': 'EUR',
    })
    # Ensure is_configured is True
    if not config.is_configured:
        config.is_configured = True
        config.save()
    return config


@pytest.fixture
def store_config(db, hub_config):
    """Create required StoreConfig for tests."""
    from apps.configuration.models import StoreConfig
    config = StoreConfig.get_solo()
    config.business_name = 'Test Store'
    config.is_configured = True  # Mark as configured to skip setup wizard
    config.save()
    return config


@pytest.fixture
def sample_product(db, store_config):
    """Create a sample product for testing."""
    from inventory.models import Category, Product

    category = Category.objects.create(
        name="Test Category",
        is_active=True
    )

    product = Product.objects.create(
        name="Test Product",
        sku="TEST-001",
        price=Decimal('10.00'),
        stock=100,
        low_stock_threshold=10,
        is_active=True
    )
    product.categories.add(category)
    return product
