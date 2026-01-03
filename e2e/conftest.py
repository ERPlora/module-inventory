"""
Playwright E2E test fixtures for inventory module.

This conftest provides common fixtures for all E2E tests in the inventory module.
All tests require authentication via PIN (1234) using the 'support' user.
"""
import pytest
from playwright.sync_api import Page, expect


# Base URL for tests (Hub running locally)
BASE_URL = "http://localhost:8001"

# Default test user and PIN
TEST_USER = "support"
TEST_PIN = "1234"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for all tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "locale": "en-US",
    }


def login_with_pin(page: Page, username: str = TEST_USER, pin: str = TEST_PIN) -> None:
    """
    Login to the Hub using PIN authentication with the 'support' user.

    This function:
    1. Navigates to the Hub
    2. Selects the 'support' employee card
    3. Enters the PIN via the keypad
    """
    page.goto(f"{BASE_URL}/")
    page.wait_for_load_state("networkidle")

    # Check if we're on login page
    if "/login" in page.url or page.locator(".login-container").count() > 0:
        # Wait for employees to load
        page.wait_for_selector(".employee-card", timeout=5000)

        # Click on the 'support' employee card (by name text)
        support_card = page.locator(f'.employee-card:has-text("{username}")')
        if support_card.count() > 0:
            support_card.first.click()
        else:
            # Fallback to first employee if 'support' not found
            page.locator(".employee-card").first.click()

        # Wait for PIN keypad to appear
        page.wait_for_selector(".keypad", timeout=3000)

        # Enter PIN digits via keypad buttons
        for digit in pin:
            page.click(f'.keypad ion-button:has-text("{digit}")')
            page.wait_for_timeout(100)  # Small delay between digits

        # Wait for navigation after successful PIN
        page.wait_for_url(f"{BASE_URL}/", timeout=5000)
        page.wait_for_load_state("networkidle")


@pytest.fixture
def authenticated_page(page: Page) -> Page:
    """
    Create an authenticated page by logging in with PIN.

    Returns the authenticated page ready for use.
    """
    login_with_pin(page)
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


@pytest.fixture
def reports_page(authenticated_page: Page) -> Page:
    """Navigate to reports page."""
    authenticated_page.goto(f"{BASE_URL}/m/inventory/reports/")
    authenticated_page.wait_for_load_state("networkidle")
    return authenticated_page


@pytest.fixture
def settings_page(authenticated_page: Page) -> Page:
    """Navigate to settings page."""
    authenticated_page.goto(f"{BASE_URL}/m/inventory/settings/")
    authenticated_page.wait_for_load_state("networkidle")
    return authenticated_page
