# Inventory Module E2E Tests

End-to-end tests for the Inventory module using Playwright.

## Prerequisites

1. Install Playwright:
```bash
pip install pytest-playwright
playwright install
```

2. Ensure Hub is running locally:
```bash
cd hub
python manage.py runserver 8001
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
```

### Run with headed browser (see the browser):
```bash
pytest e2e/ -v --headed
```

### Run with slow motion (for debugging):
```bash
pytest e2e/ -v --headed --slowmo 500
```

### Generate HTML report:
```bash
pytest e2e/ -v --html=report.html
```

## Test Structure

- `conftest.py` - Common fixtures (authentication, navigation)
- `test_dashboard.py` - Dashboard functionality tests
- `test_products.py` - Products CRUD tests
- `test_categories.py` - Categories CRUD tests

## Writing New Tests

1. Use fixtures from `conftest.py` for authentication
2. Use Playwright's `expect()` for assertions
3. Follow naming convention: `test_<action>_<expected_result>`

Example:
```python
def test_create_product_shows_success_message(products_page: Page):
    # ... test code
```

## CI/CD Integration

These tests can be run in CI with:
```bash
pytest e2e/ --browser chromium --headed=false
```
