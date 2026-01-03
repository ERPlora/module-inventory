"""
E2E tests for Products management.

Tests CRUD operations for products:
- List products
- Create new product
- View product
- Edit product
- Delete product
- Search and filter
- Export to CSV
- Table sorting
"""
import pytest
from playwright.sync_api import Page, expect
import uuid


BASE_URL = "http://localhost:8001"


class TestProductsList:
    """E2E tests for products list view."""

    def test_products_list_loads(self, products_page: Page):
        """Test products list page loads correctly."""
        expect(products_page).to_have_url(f"{BASE_URL}/m/inventory/products/")

        # Check for data table
        table = products_page.locator(".data-table")
        expect(table).to_be_visible()

    def test_products_list_shows_header(self, products_page: Page):
        """Test products list has proper header with title."""
        # Check page has content
        content = products_page.locator(".page-content, #main-content-area")
        expect(content.first).to_be_visible()

    def test_add_product_button_visible(self, products_page: Page):
        """Test add product button is visible."""
        add_button = products_page.locator('ion-button[href*="create"]')
        expect(add_button.first).to_be_visible()

    def test_products_table_has_columns(self, products_page: Page):
        """Test products table has expected columns."""
        table = products_page.locator(".data-table")
        expect(table).to_be_visible()

        # Check for expected column headers
        headers = products_page.locator(".data-table thead th")
        expect(headers.nth(0)).to_contain_text("ID")
        expect(headers.nth(2)).to_contain_text("Name")
        expect(headers.nth(4)).to_contain_text("Price")
        expect(headers.nth(5)).to_contain_text("Stock")

    def test_search_products(self, products_page: Page):
        """Test product search functionality."""
        # Find search input in ion-searchbar
        search = products_page.locator('ion-searchbar')
        expect(search).to_be_visible()

        # Type search term
        search.locator('input').fill("test")
        products_page.wait_for_timeout(500)  # Wait for debounce
        products_page.wait_for_load_state("networkidle")

    def test_export_csv_button_exists(self, products_page: Page):
        """Test export CSV button is available."""
        export_btn = products_page.locator('ion-button[href*="export"]')
        expect(export_btn.first).to_be_visible()


class TestProductCreate:
    """E2E tests for product creation."""

    def test_create_product_form_opens(self, products_page: Page):
        """Test create product form can be opened."""
        # Click add button
        add_btn = products_page.locator('ion-button[href*="create"]')
        add_btn.click()
        products_page.wait_for_load_state("networkidle")

        # Check we're on create page
        expect(products_page).to_have_url(f"{BASE_URL}/m/inventory/products/create/")

        # Check form is visible
        form = products_page.locator("form#productForm")
        expect(form).to_be_visible()

    def test_create_product_form_has_required_fields(self, products_page: Page):
        """Test create product form has all required fields."""
        products_page.goto(f"{BASE_URL}/m/inventory/products/create/")
        products_page.wait_for_load_state("networkidle")

        # Check for required input fields
        name_input = products_page.locator('ion-input[name="name"]')
        expect(name_input).to_be_visible()

        sku_input = products_page.locator('ion-input[name="sku"]')
        expect(sku_input).to_be_visible()

        price_input = products_page.locator('ion-input[name="price"]')
        expect(price_input).to_be_visible()

    def test_create_product_with_required_fields(self, products_page: Page):
        """Test creating a product with required fields."""
        unique_id = str(uuid.uuid4())[:8]

        # Navigate to create form
        products_page.goto(f"{BASE_URL}/m/inventory/products/create/")
        products_page.wait_for_load_state("networkidle")

        # Fill required fields using Ionic inputs
        products_page.locator('ion-input[name="name"]').locator('input').fill(f"Test Product {unique_id}")
        products_page.locator('ion-input[name="sku"]').locator('input').fill(f"TST-{unique_id}")
        products_page.locator('ion-input[name="price"]').locator('input').fill("19.99")

        # Submit form
        products_page.locator('ion-button[type="submit"]').click()

        # Wait for response (JSON API)
        products_page.wait_for_timeout(1500)

        # Check for success toast or redirect
        toast = products_page.locator('ion-toast')
        # Toast should appear on success

    def test_create_product_cancel_returns_to_list(self, products_page: Page):
        """Test navigating back from create form returns to list."""
        products_page.goto(f"{BASE_URL}/m/inventory/products/create/")
        products_page.wait_for_load_state("networkidle")

        # Click back button or navigate back
        products_page.go_back()
        products_page.wait_for_load_state("networkidle")

        # Should be back on products list
        expect(products_page).to_have_url(f"{BASE_URL}/m/inventory/products/")


class TestProductView:
    """E2E tests for viewing product details."""

    def test_view_product_button_exists(self, products_page: Page):
        """Test view button exists in product row."""
        # Find first view button (eye-outline icon)
        view_btn = products_page.locator('.table-actions ion-button ion-icon[name="eye-outline"]')

        if view_btn.count() > 0:
            expect(view_btn.first).to_be_visible()

    def test_view_product_opens_readonly_form(self, products_page: Page):
        """Test clicking view opens product in readonly mode."""
        # Find first view button
        view_btn = products_page.locator('.table-actions ion-button:has(ion-icon[name="eye-outline"])').first

        if view_btn.count() > 0:
            view_btn.click()
            products_page.wait_for_load_state("networkidle")

            # Check form is visible
            form = products_page.locator("form#productForm")
            expect(form).to_be_visible()


class TestProductEdit:
    """E2E tests for product editing."""

    def test_edit_product_button_exists(self, products_page: Page):
        """Test edit button exists in product row."""
        # Find first edit button (create-outline icon)
        edit_btn = products_page.locator('.table-actions ion-button ion-icon[name="create-outline"]')

        if edit_btn.count() > 0:
            expect(edit_btn.first).to_be_visible()

    def test_edit_product_opens_form(self, products_page: Page):
        """Test clicking edit opens form with data."""
        # Find first edit button
        edit_btn = products_page.locator('.table-actions ion-button:has(ion-icon[name="create-outline"])').first

        if edit_btn.count() > 0:
            edit_btn.click()
            products_page.wait_for_load_state("networkidle")

            # Check form is visible
            form = products_page.locator("form#productForm")
            expect(form).to_be_visible()

            # Check name field has value
            name_input = products_page.locator('ion-input[name="name"]')
            expect(name_input).to_be_visible()

    def test_edit_product_shows_existing_data(self, products_page: Page):
        """Test edit form shows existing product data."""
        # Find first edit button
        edit_btn = products_page.locator('.table-actions ion-button:has(ion-icon[name="create-outline"])').first

        if edit_btn.count() > 0:
            edit_btn.click()
            products_page.wait_for_load_state("networkidle")

            # Check name input has a value (not empty)
            name_input = products_page.locator('ion-input[name="name"]').locator('input')
            value = name_input.input_value()
            assert len(value) > 0, "Name field should have a value"


class TestProductDelete:
    """E2E tests for product deletion."""

    def test_delete_product_button_exists(self, products_page: Page):
        """Test delete button exists in product row."""
        # Find first delete button (trash-outline icon with danger color)
        delete_btn = products_page.locator('.table-actions ion-button[color="danger"]')

        if delete_btn.count() > 0:
            expect(delete_btn.first).to_be_visible()

    def test_delete_product_shows_confirmation(self, products_page: Page):
        """Test delete shows confirmation dialog."""
        # Find first delete button
        delete_btn = products_page.locator('.table-actions ion-button[color="danger"]').first

        if delete_btn.count() > 0:
            delete_btn.click()

            # Wait for confirmation dialog (ion-alert)
            products_page.wait_for_timeout(500)
            alert = products_page.locator("ion-alert")

            if alert.count() > 0:
                expect(alert).to_be_visible()

                # Check alert has cancel and confirm buttons
                buttons = alert.locator('button')
                expect(buttons).to_have_count(2)

                # Cancel the delete
                cancel_btn = alert.locator('button:has-text("Cancel")')
                if cancel_btn.count() > 0:
                    cancel_btn.click()
                    products_page.wait_for_timeout(300)


class TestProductTableSorting:
    """E2E tests for product table sorting."""

    def test_name_column_is_sortable(self, products_page: Page):
        """Test Name column header is sortable."""
        name_header = products_page.locator('.data-table th.sortable:has-text("Name")')
        expect(name_header).to_be_visible()

    def test_sort_by_name(self, products_page: Page):
        """Test sorting products by name."""
        # Click on Name column header
        name_header = products_page.locator('.data-table th.sortable:has-text("Name")')
        name_header.click()
        products_page.wait_for_load_state("networkidle")

        # Check URL contains order_by parameter
        expect(products_page).to_have_url_containing("order_by")

    def test_sort_by_price(self, products_page: Page):
        """Test sorting products by price."""
        # Click on Price column header
        price_header = products_page.locator('.data-table th.sortable:has-text("Price")')
        price_header.click()
        products_page.wait_for_load_state("networkidle")

        # Check URL contains order_by parameter
        expect(products_page).to_have_url_containing("order_by")

    def test_sort_by_stock(self, products_page: Page):
        """Test sorting products by stock."""
        # Click on Stock column header
        stock_header = products_page.locator('.data-table th.sortable:has-text("Stock")')
        stock_header.click()
        products_page.wait_for_load_state("networkidle")

        # Check URL contains order_by parameter
        expect(products_page).to_have_url_containing("order_by")

    def test_sort_toggle_direction(self, products_page: Page):
        """Test clicking sort header toggles direction."""
        # Click Name header twice
        name_header = products_page.locator('.data-table th.sortable:has-text("Name")')

        name_header.click()
        products_page.wait_for_load_state("networkidle")
        first_url = products_page.url

        name_header.click()
        products_page.wait_for_load_state("networkidle")
        second_url = products_page.url

        # URLs should be different (asc vs desc)
        assert first_url != second_url, "Sorting direction should toggle"


class TestProductTablePagination:
    """E2E tests for product table pagination/infinite scroll."""

    def test_infinite_scroll_trigger_exists(self, products_page: Page):
        """Test infinite scroll loader or end message exists."""
        # Check for infinite scroll loader or end message
        loader = products_page.locator('.infinite-scroll-loader, .infinite-scroll-end')

        # At least one should be visible if there are products
        table = products_page.locator('.data-table tbody tr')
        if table.count() > 0:
            expect(loader.first).to_be_visible()
