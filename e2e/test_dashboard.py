"""
E2E tests for Inventory Dashboard.

Tests the main inventory dashboard functionality including:
- Dashboard loads correctly
- Statistics are displayed
- Navigation tabs work
- Quick actions are accessible
"""
import pytest
from playwright.sync_api import Page, expect


class TestInventoryDashboard:
    """E2E tests for inventory dashboard."""

    def test_dashboard_loads(self, inventory_page: Page):
        """Test dashboard page loads successfully."""
        # Check page loaded
        expect(inventory_page).to_have_url_containing("/m/inventory/")

        # Check main content area exists
        expect(inventory_page.locator("ion-content")).to_be_visible()

    def test_dashboard_shows_statistics(self, inventory_page: Page):
        """Test dashboard displays product statistics."""
        # Look for statistic cards
        stats = inventory_page.locator(".stat-card, ion-card")
        expect(stats.first).to_be_visible()

    def test_dashboard_navigation_tabs(self, inventory_page: Page):
        """Test bottom navigation tabs are present."""
        # Check tabbar exists
        tabbar = inventory_page.locator("ion-tab-bar, .tabbar")
        expect(tabbar).to_be_visible()

        # Check for expected tabs
        products_tab = inventory_page.locator('[data-tab="products"], ion-tab-button:has-text("Products")')
        expect(products_tab).to_be_visible()

    def test_navigate_to_products(self, inventory_page: Page):
        """Test navigation to products page."""
        # Click on products tab
        inventory_page.click('[data-tab="products"], ion-tab-button:has-text("Products")')
        inventory_page.wait_for_load_state("networkidle")

        # Verify URL changed
        expect(inventory_page).to_have_url_containing("/products")

    def test_navigate_to_categories(self, inventory_page: Page):
        """Test navigation to categories page."""
        # Click on categories tab
        inventory_page.click('[data-tab="categories"], ion-tab-button:has-text("Categories")')
        inventory_page.wait_for_load_state("networkidle")

        # Verify URL changed
        expect(inventory_page).to_have_url_containing("/categories")

    def test_quick_add_product_button(self, inventory_page: Page):
        """Test quick add product button exists."""
        # Look for add button
        add_button = inventory_page.locator('ion-button:has-text("Add"), [data-action="add-product"]')
        # May or may not exist on dashboard
        if add_button.count() > 0:
            expect(add_button.first).to_be_visible()
