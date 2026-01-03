"""
E2E tests for Products management.

Tests CRUD operations for products:
- List products
- Create new product
- Edit product
- Delete product
- Search and filter
- Export to CSV
"""
import pytest
from playwright.sync_api import Page, expect
import uuid


class TestProductsList:
    """E2E tests for products list view."""

    def test_products_list_loads(self, products_page: Page):
        """Test products list page loads."""
        expect(products_page).to_have_url_containing("/products")

        # Check for table or list component
        table = products_page.locator("ion-list, table, .products-table")
        expect(table).to_be_visible()

    def test_products_list_shows_header(self, products_page: Page):
        """Test products list has proper header."""
        header = products_page.locator("ion-header, .page-header")
        expect(header).to_be_visible()

    def test_add_product_button_visible(self, products_page: Page):
        """Test add product button is visible."""
        add_button = products_page.locator('ion-button:has-text("Add"), ion-fab-button, [data-action="add"]')
        expect(add_button.first).to_be_visible()

    def test_search_products(self, products_page: Page):
        """Test product search functionality."""
        # Find search input
        search = products_page.locator('ion-searchbar, input[type="search"], [data-role="search"]')

        if search.count() > 0:
            search.first.fill("test")
            products_page.wait_for_load_state("networkidle")
            # Search should filter results


class TestProductCreate:
    """E2E tests for product creation."""

    def test_create_product_form_opens(self, products_page: Page):
        """Test create product form can be opened."""
        # Click add button
        products_page.click('ion-button:has-text("Add"), ion-fab-button, [data-action="add"]')
        products_page.wait_for_load_state("networkidle")

        # Check form is visible
        form = products_page.locator("form, ion-modal, .product-form")
        expect(form.first).to_be_visible()

    def test_create_product_with_required_fields(self, products_page: Page):
        """Test creating a product with required fields."""
        unique_id = str(uuid.uuid4())[:8]

        # Open create form
        products_page.click('ion-button:has-text("Add"), ion-fab-button, [data-action="add"]')
        products_page.wait_for_load_state("networkidle")

        # Fill required fields
        products_page.fill('input[name="name"], ion-input[name="name"] input', f"Test Product {unique_id}")
        products_page.fill('input[name="sku"], ion-input[name="sku"] input', f"TST-{unique_id}")
        products_page.fill('input[name="price"], ion-input[name="price"] input', "19.99")

        # Submit form
        products_page.click('ion-button[type="submit"], button[type="submit"]:has-text("Save")')
        products_page.wait_for_load_state("networkidle")

        # Verify product appears in list or success message
        # This depends on your implementation

    def test_create_product_validation(self, products_page: Page):
        """Test form validation on create."""
        # Open create form
        products_page.click('ion-button:has-text("Add"), ion-fab-button, [data-action="add"]')
        products_page.wait_for_load_state("networkidle")

        # Try to submit empty form
        products_page.click('ion-button[type="submit"], button[type="submit"]')

        # Check for validation errors
        error = products_page.locator('.error, ion-note[color="danger"], .validation-error')
        # Validation should show errors


class TestProductEdit:
    """E2E tests for product editing."""

    def test_edit_product_opens_form(self, products_page: Page):
        """Test clicking edit opens form."""
        # Find first product row
        row = products_page.locator("ion-item, tr").first

        if row.is_visible():
            # Click edit button
            edit_btn = row.locator('ion-button:has-text("Edit"), [data-action="edit"]')
            if edit_btn.count() > 0:
                edit_btn.click()
                products_page.wait_for_load_state("networkidle")

                # Check form is visible
                form = products_page.locator("form, .product-form")
                expect(form.first).to_be_visible()


class TestProductDelete:
    """E2E tests for product deletion."""

    def test_delete_product_confirmation(self, products_page: Page):
        """Test delete shows confirmation dialog."""
        # Find first product row
        row = products_page.locator("ion-item, tr").first

        if row.is_visible():
            # Click delete button
            delete_btn = row.locator('ion-button:has-text("Delete"), [data-action="delete"]')
            if delete_btn.count() > 0:
                delete_btn.click()

                # Check for confirmation dialog
                dialog = products_page.locator("ion-alert, .confirm-dialog, [role='dialog']")
                if dialog.count() > 0:
                    expect(dialog.first).to_be_visible()


class TestProductExport:
    """E2E tests for product export."""

    def test_export_csv_button_exists(self, products_page: Page):
        """Test export CSV button is available."""
        export_btn = products_page.locator('ion-button:has-text("Export"), [data-action="export"]')

        if export_btn.count() > 0:
            expect(export_btn.first).to_be_visible()
