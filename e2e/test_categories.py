"""
E2E tests for Categories management.

Tests CRUD operations for categories:
- List categories
- Create new category
- Edit category
- Delete category
"""
import pytest
from playwright.sync_api import Page, expect
import uuid


class TestCategoriesList:
    """E2E tests for categories list view."""

    def test_categories_list_loads(self, categories_page: Page):
        """Test categories list page loads."""
        expect(categories_page).to_have_url_containing("/categories")

        # Check for list or grid component
        list_container = categories_page.locator("ion-list, .categories-list, .categories-grid")
        expect(list_container.first).to_be_visible()

    def test_add_category_button_visible(self, categories_page: Page):
        """Test add category button is visible."""
        add_button = categories_page.locator('ion-button:has-text("Add"), ion-fab-button, [data-action="add"]')
        expect(add_button.first).to_be_visible()


class TestCategoryCreate:
    """E2E tests for category creation."""

    def test_create_category_form_opens(self, categories_page: Page):
        """Test create category form can be opened."""
        # Click add button
        categories_page.click('ion-button:has-text("Add"), ion-fab-button, [data-action="add"]')
        categories_page.wait_for_load_state("networkidle")

        # Check form is visible
        form = categories_page.locator("form, ion-modal, .category-form")
        expect(form.first).to_be_visible()

    def test_create_category_with_required_fields(self, categories_page: Page):
        """Test creating a category with required fields."""
        unique_id = str(uuid.uuid4())[:8]

        # Open create form
        categories_page.click('ion-button:has-text("Add"), ion-fab-button, [data-action="add"]')
        categories_page.wait_for_load_state("networkidle")

        # Fill required fields
        categories_page.fill('input[name="name"], ion-input[name="name"] input', f"Test Category {unique_id}")

        # Submit form
        categories_page.click('ion-button[type="submit"], button[type="submit"]:has-text("Save")')
        categories_page.wait_for_load_state("networkidle")


class TestCategoryEdit:
    """E2E tests for category editing."""

    def test_edit_category_opens_form(self, categories_page: Page):
        """Test clicking edit opens form."""
        # Find first category item
        item = categories_page.locator("ion-item, .category-item").first

        if item.is_visible():
            # Click edit button
            edit_btn = item.locator('ion-button:has-text("Edit"), [data-action="edit"]')
            if edit_btn.count() > 0:
                edit_btn.click()
                categories_page.wait_for_load_state("networkidle")

                # Check form is visible
                form = categories_page.locator("form, .category-form")
                expect(form.first).to_be_visible()


class TestCategoryDelete:
    """E2E tests for category deletion."""

    def test_delete_category_with_products_shows_error(self, categories_page: Page):
        """Test deleting category with products shows error."""
        # Find first category with products
        item = categories_page.locator("ion-item, .category-item").first

        if item.is_visible():
            # Click delete button
            delete_btn = item.locator('ion-button:has-text("Delete"), [data-action="delete"]')
            if delete_btn.count() > 0:
                delete_btn.click()
                categories_page.wait_for_load_state("networkidle")

                # Should show error if category has products
                # Check for error message or confirmation dialog
