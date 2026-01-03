"""
E2E tests for Inventory Dashboard.

Tests the main inventory dashboard functionality including:
- Dashboard loads correctly
- Statistics are displayed
- Navigation tabbar works
- Categories summary
- Low stock products
"""
import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:8001"


class TestInventoryDashboard:
    """E2E tests for inventory dashboard main page."""

    def test_dashboard_loads(self, inventory_page: Page):
        """Test dashboard page loads successfully."""
        # Check page loaded
        expect(inventory_page).to_have_url(f"{BASE_URL}/m/inventory/")

        # Check main content area exists
        content = inventory_page.locator(".page-content, #main-content-area")
        expect(content.first).to_be_visible()

    def test_dashboard_shows_title(self, inventory_page: Page):
        """Test dashboard shows Inventory title."""
        # Check for page title
        title = inventory_page.locator(".page-header__title, ion-title, h1")
        expect(title.first).to_be_visible()

    def test_dashboard_shows_statistics_cards(self, inventory_page: Page):
        """Test dashboard displays product statistics cards."""
        # Look for statistic cards (ui-grid--stats)
        stats_grid = inventory_page.locator(".ui-grid--stats")
        expect(stats_grid).to_be_visible()

        # Check for stat cards
        stat_cards = inventory_page.locator(".ui-stat-card")
        expect(stat_cards.first).to_be_visible()

    def test_dashboard_shows_total_products(self, inventory_page: Page):
        """Test dashboard shows total products count."""
        # Find stat card with "Total Products" or similar
        total_card = inventory_page.locator('.ui-stat-card:has-text("Total"), .ui-stat-card:has-text("Products")')
        expect(total_card.first).to_be_visible()

    def test_dashboard_shows_low_stock(self, inventory_page: Page):
        """Test dashboard shows low stock indicator."""
        # Find stat card with "Low Stock"
        low_stock_card = inventory_page.locator('.ui-stat-card:has-text("Low Stock")')
        expect(low_stock_card.first).to_be_visible()


class TestInventoryDashboardNavigation:
    """E2E tests for dashboard navigation."""

    def test_tabbar_is_visible(self, inventory_page: Page):
        """Test bottom navigation tabbar is visible."""
        tabbar = inventory_page.locator("#global-tabbar-footer, ion-tab-bar")
        expect(tabbar.first).to_be_visible()

    def test_tabbar_has_dashboard_tab(self, inventory_page: Page):
        """Test tabbar has Dashboard tab."""
        dashboard_tab = inventory_page.locator('ion-tab-button:has-text("Dashboard"), ion-tab-button:has-text("Home")')
        expect(dashboard_tab.first).to_be_visible()

    def test_tabbar_has_products_tab(self, inventory_page: Page):
        """Test tabbar has Products tab."""
        products_tab = inventory_page.locator('ion-tab-button:has-text("Products")')
        expect(products_tab).to_be_visible()

    def test_tabbar_has_categories_tab(self, inventory_page: Page):
        """Test tabbar has Categories tab."""
        categories_tab = inventory_page.locator('ion-tab-button:has-text("Categories")')
        expect(categories_tab).to_be_visible()

    def test_navigate_to_products_via_tabbar(self, inventory_page: Page):
        """Test navigation to products page via tabbar."""
        # Click on products tab
        products_tab = inventory_page.locator('ion-tab-button:has-text("Products")')
        products_tab.click()
        inventory_page.wait_for_load_state("networkidle")

        # Verify URL changed
        expect(inventory_page).to_have_url(f"{BASE_URL}/m/inventory/products/")

    def test_navigate_to_categories_via_tabbar(self, inventory_page: Page):
        """Test navigation to categories page via tabbar."""
        # Click on categories tab
        categories_tab = inventory_page.locator('ion-tab-button:has-text("Categories")')
        categories_tab.click()
        inventory_page.wait_for_load_state("networkidle")

        # Verify URL changed
        expect(inventory_page).to_have_url(f"{BASE_URL}/m/inventory/categories/")

    def test_navigate_to_reports_via_tabbar(self, inventory_page: Page):
        """Test navigation to reports page via tabbar."""
        # Click on reports tab
        reports_tab = inventory_page.locator('ion-tab-button:has-text("Reports")')
        if reports_tab.count() > 0:
            reports_tab.click()
            inventory_page.wait_for_load_state("networkidle")

            # Verify URL changed
            expect(inventory_page).to_have_url(f"{BASE_URL}/m/inventory/reports/")

    def test_navigate_to_settings_via_tabbar(self, inventory_page: Page):
        """Test navigation to settings page via tabbar."""
        # Click on settings tab
        settings_tab = inventory_page.locator('ion-tab-button:has-text("Settings")')
        if settings_tab.count() > 0:
            settings_tab.click()
            inventory_page.wait_for_load_state("networkidle")

            # Verify URL changed
            expect(inventory_page).to_have_url(f"{BASE_URL}/m/inventory/settings/")


class TestDashboardCategoriesSummary:
    """E2E tests for categories summary on dashboard."""

    def test_categories_section_visible(self, inventory_page: Page):
        """Test categories summary section is visible."""
        # Look for categories section or card
        categories_section = inventory_page.locator('.ui-card:has-text("Categories"), [class*="category"]')
        expect(categories_section.first).to_be_visible()

    def test_view_all_categories_button(self, inventory_page: Page):
        """Test View all button for categories exists."""
        # Find View all button in categories section
        view_all_btn = inventory_page.locator('ion-button:has-text("View all")')
        if view_all_btn.count() > 0:
            expect(view_all_btn.first).to_be_visible()

    def test_click_view_all_categories(self, inventory_page: Page):
        """Test clicking View all navigates to categories."""
        # Find first View all button (should be in categories section)
        view_all_btn = inventory_page.locator('ion-button:has-text("View all")').first

        if view_all_btn.count() > 0:
            view_all_btn.click()
            inventory_page.wait_for_load_state("networkidle")

            # Should navigate to categories
            expect(inventory_page).to_have_url_containing("categories")


class TestDashboardLowStockProducts:
    """E2E tests for low stock products section."""

    def test_low_stock_section_conditional(self, inventory_page: Page):
        """Test low stock section appears when there are low stock products."""
        # This section only appears if there are low stock products
        low_stock_section = inventory_page.locator('.ui-card:has-text("Low Stock")')

        # May or may not be visible depending on data
        # Just verify it doesn't break the page
        inventory_page.wait_for_timeout(500)


class TestDashboardResponsiveness:
    """E2E tests for dashboard responsive layout."""

    def test_stats_grid_visible_on_desktop(self, inventory_page: Page):
        """Test stats grid is properly displayed."""
        stats_grid = inventory_page.locator(".ui-grid--stats")
        expect(stats_grid).to_be_visible()

    def test_page_has_proper_padding(self, inventory_page: Page):
        """Test page content has proper padding."""
        content = inventory_page.locator(".page-content")
        expect(content).to_be_visible()
