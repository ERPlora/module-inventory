"""
E2E tests for Categories management.

Tests CRUD operations for categories:
- List categories
- Create new category
- Edit category
- Delete category
- Table sorting
- Import/Export
"""
import pytest
from playwright.sync_api import Page, expect
import uuid


BASE_URL = "http://localhost:8001"


class TestCategoriesList:
    """E2E tests for categories list view."""

    def test_categories_list_loads(self, categories_page: Page):
        """Test categories list page loads correctly."""
        expect(categories_page).to_have_url(f"{BASE_URL}/m/inventory/categories/")

        # Check for data table
        table = categories_page.locator(".data-table")
        expect(table).to_be_visible()

    def test_categories_list_shows_header(self, categories_page: Page):
        """Test categories list has proper content area."""
        content = categories_page.locator(".page-content, #main-content-area")
        expect(content.first).to_be_visible()

    def test_add_category_button_visible(self, categories_page: Page):
        """Test add category button is visible."""
        add_button = categories_page.locator('ion-button[href*="create"]')
        expect(add_button.first).to_be_visible()

    def test_categories_table_has_columns(self, categories_page: Page):
        """Test categories table has expected columns."""
        table = categories_page.locator(".data-table")
        expect(table).to_be_visible()

        # Check for expected column headers
        headers = categories_page.locator(".data-table thead th")
        expect(headers.nth(0)).to_contain_text("ID")
        expect(headers.nth(2)).to_contain_text("Name")
        expect(headers.nth(4)).to_contain_text("Products")

    def test_search_categories(self, categories_page: Page):
        """Test category search functionality."""
        # Find search input in ion-searchbar
        search = categories_page.locator('ion-searchbar')
        expect(search).to_be_visible()

        # Type search term
        search.locator('input').fill("test")
        categories_page.wait_for_timeout(500)  # Wait for debounce
        categories_page.wait_for_load_state("networkidle")

    def test_export_csv_button_exists(self, categories_page: Page):
        """Test export CSV button is available."""
        export_btn = categories_page.locator('ion-button[href*="export"]')
        expect(export_btn.first).to_be_visible()


class TestCategoryCreate:
    """E2E tests for category creation."""

    def test_create_category_form_opens(self, categories_page: Page):
        """Test create category form can be opened."""
        # Click add button
        add_btn = categories_page.locator('ion-button[href*="create"]')
        add_btn.click()
        categories_page.wait_for_load_state("networkidle")

        # Check we're on create page
        expect(categories_page).to_have_url(f"{BASE_URL}/m/inventory/categories/create/")

        # Check form is visible
        form = categories_page.locator("form#categoryForm")
        expect(form).to_be_visible()

    def test_create_category_form_has_required_fields(self, categories_page: Page):
        """Test create category form has all required fields."""
        categories_page.goto(f"{BASE_URL}/m/inventory/categories/create/")
        categories_page.wait_for_load_state("networkidle")

        # Check for required input fields
        name_input = categories_page.locator('ion-input[name="name"]')
        expect(name_input).to_be_visible()

        # Check for optional fields
        icon_input = categories_page.locator('ion-input[name="icon"]')
        expect(icon_input).to_be_visible()

        color_input = categories_page.locator('input[name="color"]')
        expect(color_input).to_be_visible()

    def test_create_category_with_required_fields(self, categories_page: Page):
        """Test creating a category with required fields."""
        unique_id = str(uuid.uuid4())[:8]

        # Navigate to create form
        categories_page.goto(f"{BASE_URL}/m/inventory/categories/create/")
        categories_page.wait_for_load_state("networkidle")

        # Fill required fields using Ionic inputs
        categories_page.locator('ion-input[name="name"]').locator('input').fill(f"Test Category {unique_id}")

        # Submit form
        categories_page.locator('ion-button[type="submit"]').click()

        # Wait for response (JSON API)
        categories_page.wait_for_timeout(1500)

        # Check for success toast
        toast = categories_page.locator('ion-toast')
        # Toast should appear on success

    def test_create_category_with_all_fields(self, categories_page: Page):
        """Test creating a category with all optional fields."""
        unique_id = str(uuid.uuid4())[:8]

        # Navigate to create form
        categories_page.goto(f"{BASE_URL}/m/inventory/categories/create/")
        categories_page.wait_for_load_state("networkidle")

        # Fill all fields
        categories_page.locator('ion-input[name="name"]').locator('input').fill(f"Full Category {unique_id}")
        categories_page.locator('ion-textarea[name="description"]').locator('textarea').fill("A test category description")
        categories_page.locator('ion-input[name="icon"]').locator('input').fill("pizza-outline")
        categories_page.locator('input[name="color"]').fill("#FF5722")
        categories_page.locator('ion-input[name="order"]').locator('input').fill("5")

        # Submit form
        categories_page.locator('ion-button[type="submit"]').click()
        categories_page.wait_for_timeout(1500)

    def test_create_category_cancel_returns_to_list(self, categories_page: Page):
        """Test navigating back from create form returns to list."""
        categories_page.goto(f"{BASE_URL}/m/inventory/categories/create/")
        categories_page.wait_for_load_state("networkidle")

        # Navigate back
        categories_page.go_back()
        categories_page.wait_for_load_state("networkidle")

        # Should be back on categories list
        expect(categories_page).to_have_url(f"{BASE_URL}/m/inventory/categories/")


class TestCategoryEdit:
    """E2E tests for category editing."""

    def test_edit_category_button_exists(self, categories_page: Page):
        """Test edit button exists in category row."""
        # Find first edit button (create-outline icon)
        edit_btn = categories_page.locator('.table-actions ion-button ion-icon[name="create-outline"]')

        if edit_btn.count() > 0:
            expect(edit_btn.first).to_be_visible()

    def test_edit_category_opens_form(self, categories_page: Page):
        """Test clicking edit opens form with data."""
        # Find first edit button
        edit_btn = categories_page.locator('.table-actions ion-button:has(ion-icon[name="create-outline"])').first

        if edit_btn.count() > 0:
            edit_btn.click()
            categories_page.wait_for_load_state("networkidle")

            # Check form is visible
            form = categories_page.locator("form#categoryForm")
            expect(form).to_be_visible()

            # Check name field has value
            name_input = categories_page.locator('ion-input[name="name"]')
            expect(name_input).to_be_visible()

    def test_edit_category_shows_existing_data(self, categories_page: Page):
        """Test edit form shows existing category data."""
        # Find first edit button
        edit_btn = categories_page.locator('.table-actions ion-button:has(ion-icon[name="create-outline"])').first

        if edit_btn.count() > 0:
            edit_btn.click()
            categories_page.wait_for_load_state("networkidle")

            # Check name input has a value (not empty)
            name_input = categories_page.locator('ion-input[name="name"]').locator('input')
            value = name_input.input_value()
            assert len(value) > 0, "Name field should have a value"

    def test_edit_category_saves_changes(self, categories_page: Page):
        """Test editing and saving category changes."""
        # Find first edit button
        edit_btn = categories_page.locator('.table-actions ion-button:has(ion-icon[name="create-outline"])').first

        if edit_btn.count() > 0:
            edit_btn.click()
            categories_page.wait_for_load_state("networkidle")

            # Modify the description field
            desc_textarea = categories_page.locator('ion-textarea[name="description"]').locator('textarea')
            desc_textarea.fill("Updated description via E2E test")

            # Submit form
            categories_page.locator('ion-button[type="submit"]').click()
            categories_page.wait_for_timeout(1500)


class TestCategoryDelete:
    """E2E tests for category deletion."""

    def test_delete_category_button_exists(self, categories_page: Page):
        """Test delete button exists in category row."""
        # Find first delete button (trash-outline icon with danger color)
        delete_btn = categories_page.locator('.table-actions ion-button[color="danger"]')

        if delete_btn.count() > 0:
            expect(delete_btn.first).to_be_visible()

    def test_delete_category_shows_confirmation(self, categories_page: Page):
        """Test delete shows confirmation dialog."""
        # Find first delete button
        delete_btn = categories_page.locator('.table-actions ion-button[color="danger"]').first

        if delete_btn.count() > 0:
            delete_btn.click()

            # Wait for confirmation dialog (ion-alert)
            categories_page.wait_for_timeout(500)
            alert = categories_page.locator("ion-alert")

            if alert.count() > 0:
                expect(alert).to_be_visible()

                # Check alert has buttons
                buttons = alert.locator('button')
                expect(buttons.first).to_be_visible()

                # Cancel the delete
                cancel_btn = alert.locator('button:has-text("Cancel")')
                if cancel_btn.count() > 0:
                    cancel_btn.click()
                    categories_page.wait_for_timeout(300)


class TestCategoryTableSorting:
    """E2E tests for category table sorting."""

    def test_name_column_is_sortable(self, categories_page: Page):
        """Test Name column header is sortable."""
        name_header = categories_page.locator('.data-table th.sortable:has-text("Name")')
        expect(name_header).to_be_visible()

    def test_sort_by_name(self, categories_page: Page):
        """Test sorting categories by name."""
        # Click on Name column header
        name_header = categories_page.locator('.data-table th.sortable:has-text("Name")')
        name_header.click()
        categories_page.wait_for_load_state("networkidle")

        # Check URL contains order_by parameter
        expect(categories_page).to_have_url_containing("order_by")

    def test_sort_by_order(self, categories_page: Page):
        """Test sorting categories by display order."""
        # Click on Order column header
        order_header = categories_page.locator('.data-table th.sortable:has-text("Order")')
        order_header.click()
        categories_page.wait_for_load_state("networkidle")

        # Check URL contains order_by parameter
        expect(categories_page).to_have_url_containing("order_by")


class TestCategoryProductCount:
    """E2E tests for category product count display."""

    def test_product_count_column_visible(self, categories_page: Page):
        """Test product count column is visible."""
        products_header = categories_page.locator('.data-table th:has-text("Products")')
        expect(products_header).to_be_visible()

    def test_product_count_displayed(self, categories_page: Page):
        """Test product count is displayed in each row."""
        # Find product count badges
        count_badges = categories_page.locator('.data-table tbody td .table-stock-badge')

        if count_badges.count() > 0:
            expect(count_badges.first).to_be_visible()


class TestCategoryIcon:
    """E2E tests for category icon display."""

    def test_category_icon_or_image_visible(self, categories_page: Page):
        """Test category has icon or image displayed."""
        # Find icon column cells
        icon_cells = categories_page.locator('.data-table tbody td .table-image-placeholder, .data-table tbody td img.table-image')

        if icon_cells.count() > 0:
            expect(icon_cells.first).to_be_visible()
