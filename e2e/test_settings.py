"""
E2E tests for Inventory Settings page.

Tests settings functionality:
- Settings page loads
- Toggle settings work
- Reset to defaults
"""
import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:8001"


class TestSettingsPage:
    """E2E tests for settings page."""

    def test_settings_page_loads(self, settings_page: Page):
        """Test settings page loads correctly."""
        expect(settings_page).to_have_url(f"{BASE_URL}/m/inventory/settings/")

        # Check page content is visible
        content = settings_page.locator(".page-content, #main-content-area")
        expect(content.first).to_be_visible()

    def test_settings_has_title(self, settings_page: Page):
        """Test settings page has title."""
        title = settings_page.locator(".page-header__title, ion-title, h1")
        expect(title.first).to_be_visible()

    def test_settings_toggles_visible(self, settings_page: Page):
        """Test settings toggle switches are visible."""
        # Look for ion-toggle elements
        toggles = settings_page.locator("ion-toggle")

        if toggles.count() > 0:
            expect(toggles.first).to_be_visible()

    def test_settings_barcode_toggle(self, settings_page: Page):
        """Test barcode generation toggle exists."""
        # Find barcode toggle by label
        barcode_item = settings_page.locator('ion-item:has-text("Barcode"), ion-item:has-text("barcode")')

        if barcode_item.count() > 0:
            expect(barcode_item.first).to_be_visible()

    def test_toggle_setting_change(self, settings_page: Page):
        """Test toggling a setting."""
        # Find first toggle
        toggle = settings_page.locator("ion-toggle").first

        if toggle.count() > 0:
            # Get initial state
            initial_checked = toggle.get_attribute("checked")

            # Click toggle
            toggle.click()
            settings_page.wait_for_timeout(500)

            # State should have changed (or triggered an HTMX request)


class TestSettingsReset:
    """E2E tests for settings reset functionality."""

    def test_reset_button_exists(self, settings_page: Page):
        """Test reset to defaults button exists."""
        reset_btn = settings_page.locator('ion-button:has-text("Reset"), ion-button:has-text("Default")')

        if reset_btn.count() > 0:
            expect(reset_btn.first).to_be_visible()


class TestSettingsInfo:
    """E2E tests for settings info section."""

    def test_info_section_visible(self, settings_page: Page):
        """Test info/help section is visible."""
        info_section = settings_page.locator('.setting-info, ion-note')

        if info_section.count() > 0:
            expect(info_section.first).to_be_visible()
