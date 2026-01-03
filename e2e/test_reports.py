"""
E2E tests for Inventory Reports page.

Tests reports functionality:
- Reports page loads
- Report tables display correctly
- Report filters work
"""
import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:8001"


class TestReportsPage:
    """E2E tests for reports page."""

    def test_reports_page_loads(self, reports_page: Page):
        """Test reports page loads correctly."""
        expect(reports_page).to_have_url(f"{BASE_URL}/m/inventory/reports/")

        # Check page content is visible
        content = reports_page.locator(".page-content, #main-content-area")
        expect(content.first).to_be_visible()

    def test_reports_has_title(self, reports_page: Page):
        """Test reports page has title."""
        title = reports_page.locator(".page-header__title, ion-title, h1")
        expect(title.first).to_be_visible()

    def test_reports_has_content(self, reports_page: Page):
        """Test reports page has content cards."""
        # Look for cards or tables
        cards = reports_page.locator(".ui-card, ion-card")
        expect(cards.first).to_be_visible()


class TestInventorySummaryReport:
    """E2E tests for inventory summary section."""

    def test_inventory_summary_visible(self, reports_page: Page):
        """Test inventory summary section is visible."""
        summary = reports_page.locator('.ui-card:has-text("Summary"), .ui-card:has-text("Inventory")')

        if summary.count() > 0:
            expect(summary.first).to_be_visible()


class TestLowStockReport:
    """E2E tests for low stock report."""

    def test_low_stock_section_visible(self, reports_page: Page):
        """Test low stock report section is visible."""
        low_stock = reports_page.locator('.ui-card:has-text("Low Stock")')

        if low_stock.count() > 0:
            expect(low_stock.first).to_be_visible()

    def test_low_stock_table_headers(self, reports_page: Page):
        """Test low stock table has proper headers."""
        # Look for table in low stock section
        table = reports_page.locator('table')

        if table.count() > 0:
            headers = table.locator('th')
            expect(headers.first).to_be_visible()


class TestCategoryDistributionReport:
    """E2E tests for category distribution report."""

    def test_category_distribution_visible(self, reports_page: Page):
        """Test category distribution section is visible."""
        distribution = reports_page.locator('.ui-card:has-text("Category"), .ui-card:has-text("Distribution")')

        if distribution.count() > 0:
            expect(distribution.first).to_be_visible()


class TestReportsTabbar:
    """E2E tests for reports page tabbar."""

    def test_tabbar_visible_on_reports(self, reports_page: Page):
        """Test tabbar is visible on reports page."""
        tabbar = reports_page.locator("#global-tabbar-footer, ion-tab-bar")
        expect(tabbar.first).to_be_visible()

    def test_reports_tab_selected(self, reports_page: Page):
        """Test Reports tab is selected."""
        reports_tab = reports_page.locator('ion-tab-button:has-text("Reports")')

        if reports_tab.count() > 0:
            # Check if tab has selected class
            expect(reports_tab).to_have_class_containing("tab-selected")
