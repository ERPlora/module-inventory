"""
Playwright E2E test fixtures for inventory module.

This conftest provides common fixtures for all E2E tests in the inventory module.
"""
import pytest
from playwright.sync_api import Page, expect


# Base URL for tests (Hub running locally)
BASE_URL = "http://localhost:8001"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for all tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "locale": "en-US",
    }


@pytest.fixture
def authenticated_page(page: Page) -> Page:
    """
    Create an authenticated page by logging in.

    This fixture:
    1. Navigates to the Hub
    2. Logs in with test credentials
    3. Sets up PIN if needed
    4. Returns the authenticated page
    """
    # Navigate to Hub
    page.goto(f"{BASE_URL}/")

    # Wait for redirect to login or main page
    page.wait_for_load_state("networkidle")

    # Check if we need to log in
    if "/login" in page.url or "/cloud-login" in page.url:
        # For local development, we may have a PIN-only flow
        # This will need customization based on your auth setup
        pass

    # If we're on PIN verification page
    if "/verify-pin" in page.url:
        # Enter PIN (adjust selector based on your UI)
        page.fill('input[type="password"]', '1234')
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

    return page


@pytest.fixture
def inventory_page(authenticated_page: Page) -> Page:
    """Navigate to inventory module dashboard."""
    authenticated_page.goto(f"{BASE_URL}/m/inventory/")
    authenticated_page.wait_for_load_state("networkidle")
    return authenticated_page


@pytest.fixture
def products_page(authenticated_page: Page) -> Page:
    """Navigate to products list page."""
    authenticated_page.goto(f"{BASE_URL}/m/inventory/products/")
    authenticated_page.wait_for_load_state("networkidle")
    return authenticated_page


@pytest.fixture
def categories_page(authenticated_page: Page) -> Page:
    """Navigate to categories page."""
    authenticated_page.goto(f"{BASE_URL}/m/inventory/categories/")
    authenticated_page.wait_for_load_state("networkidle")
    return authenticated_page
