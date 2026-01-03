# Inventory Module E2E Tests

End-to-end tests for the Inventory module using Playwright.

## Prerequisites

1. Install Playwright:
```bash
pip install pytest-playwright
playwright install chromium
```

2. Ensure Hub is running locally:
```bash
cd hub
source .venv/bin/activate
python manage.py runserver 8001
```

3. Ensure the `support` user exists with PIN `1234` (or adjust `TEST_USER` and `TEST_PIN` in conftest.py)

## Test Structure

```
e2e/
├── conftest.py          # Common fixtures (authentication, navigation)
├── test_dashboard.py    # Dashboard functionality tests
├── test_products.py     # Products CRUD tests
├── test_categories.py   # Categories CRUD tests
├── test_reports.py      # Reports page tests
├── test_settings.py     # Settings page tests
└── README.md           # This file
```

## Running Tests

### Run all E2E tests:
```bash
cd modules/inventory
pytest e2e/ -v
```

### Run specific test file:
```bash
pytest e2e/test_dashboard.py -v
pytest e2e/test_products.py -v
pytest e2e/test_categories.py -v
```

### Run with headed browser (see the browser):
```bash
pytest e2e/ -v --headed
```

### Run with slow motion (for debugging):
```bash
pytest e2e/ -v --headed --slowmo 500
```

### Run specific test class:
```bash
pytest e2e/test_products.py::TestProductCreate -v
```

### Run specific test:
```bash
pytest e2e/test_products.py::TestProductCreate::test_create_product_form_opens -v
```

### Generate HTML report:
```bash
pytest e2e/ -v --html=report.html
```

## Authentication

All tests use PIN authentication with the `support` user. The `conftest.py` handles:

1. Navigate to Hub (http://localhost:8001)
2. Select the `support` employee card on login page
3. Enter PIN `1234` via keypad
4. Wait for redirect to main page

To change the user or PIN, modify `TEST_USER` and `TEST_PIN` in `conftest.py`.

## Writing New Tests

1. Use fixtures from `conftest.py` for authentication:
   - `authenticated_page` - Base authenticated page
   - `inventory_page` - Dashboard page
   - `products_page` - Products list
   - `categories_page` - Categories list
   - `reports_page` - Reports page
   - `settings_page` - Settings page

2. Use Playwright's `expect()` for assertions

3. Follow naming convention: `test_<action>_<expected_result>`

Example:
```python
def test_create_product_shows_success_message(products_page: Page):
    # Navigate to create form
    products_page.goto(f"{BASE_URL}/m/inventory/products/create/")
    products_page.wait_for_load_state("networkidle")

    # Fill form
    products_page.locator('ion-input[name="name"]').locator('input').fill("New Product")

    # Submit
    products_page.locator('ion-button[type="submit"]').click()

    # Verify toast
    toast = products_page.locator('ion-toast')
    expect(toast).to_be_visible()
```

## Ionic Components

When working with Ionic components, use these patterns:

```python
# ion-input - access inner input
products_page.locator('ion-input[name="name"]').locator('input').fill("value")

# ion-searchbar - access inner input
products_page.locator('ion-searchbar').locator('input').fill("search term")

# ion-button with href
products_page.locator('ion-button[href*="create"]').click()

# ion-button by icon
products_page.locator('ion-button:has(ion-icon[name="create-outline"])').click()

# ion-alert
alert = products_page.locator("ion-alert")
alert.locator('button:has-text("Cancel")').click()

# ion-toggle
toggle = products_page.locator("ion-toggle").first
toggle.click()
```

## CI/CD Integration

Run in headless mode for CI:
```bash
pytest e2e/ --browser chromium
```

With specific viewport:
```bash
pytest e2e/ --browser chromium --viewport-width 1280 --viewport-height 720
```

## Troubleshooting

### Tests fail at login
- Ensure Hub is running on port 8001
- Verify a user with PIN `1234` exists
- Check browser console for errors

### Element not found
- Use `--headed --slowmo 500` to debug
- Verify selectors match actual DOM
- Wait for network idle: `page.wait_for_load_state("networkidle")`

### Timeout errors
- Increase timeout: `page.wait_for_selector(".element", timeout=10000)`
- Check for HTMX requests completing
