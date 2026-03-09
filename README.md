# Inventory

## Overview

| Property | Value |
|----------|-------|
| **Module ID** | `inventory` |
| **Version** | `1.0.0` |
| **Icon** | `cube-outline` |
| **Dependencies** | None |

## Models

### `InventorySettings`

Per-hub inventory settings.

| Field | Type | Details |
|-------|------|---------|
| `allow_negative_stock` | BooleanField |  |
| `low_stock_alert_enabled` | BooleanField |  |
| `auto_generate_sku` | BooleanField |  |
| `barcode_enabled` | BooleanField |  |

**Methods:**

- `get_settings()` — Get or create settings for a hub.

### `Category`

Product category.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=100 |
| `code` | CharField | max_length=100, optional |
| `slug` | SlugField | max_length=100, optional |
| `icon` | CharField | max_length=50 |
| `color` | CharField | max_length=7 |
| `image` | ImageField | max_length=100, optional |
| `description` | TextField | optional |
| `tax_class` | ForeignKey | → `configuration.TaxClass`, on_delete=SET_NULL, optional |
| `is_active` | BooleanField |  |
| `sort_order` | PositiveIntegerField |  |

**Methods:**

- `get_image_url()`
- `get_initial()`

**Properties:**

- `product_count`

### `Product`

Product in the catalogue.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=255 |
| `sku` | CharField | max_length=100 |
| `ean13` | CharField | max_length=13, optional |
| `description` | TextField | optional |
| `product_type` | CharField | max_length=20, choices: physical, service |
| `source` | CharField | max_length=20, choices: user, blueprint, import |
| `price` | DecimalField |  |
| `cost` | DecimalField |  |
| `stock` | IntegerField |  |
| `low_stock_threshold` | PositiveIntegerField |  |
| `tax_class` | ForeignKey | → `configuration.TaxClass`, on_delete=SET_NULL, optional |
| `image` | ImageField | max_length=100, optional |
| `allergens` | JSONField | optional |
| `is_active` | BooleanField |  |
| `categories` | ManyToManyField | → `inventory.Category`, optional |

**Methods:**

- `get_effective_tax_class()` — Tax class inheritance: Product -> Category -> StoreConfig.default_tax_class.
- `get_tax_rate()` — Effective tax rate as percentage (e.g. 21.00).
- `get_image_path()`
- `get_initial()`

**Properties:**

- `is_low_stock`
- `allergen_names` — Return display names for active allergens.
- `has_allergens`
- `profit_margin`
- `is_service`

### `ProductVariant`

Variant of a product (colour, size, weight, etc.).

| Field | Type | Details |
|-------|------|---------|
| `product` | ForeignKey | → `inventory.Product`, on_delete=CASCADE |
| `name` | CharField | max_length=255 |
| `sku` | CharField | max_length=100 |
| `attributes` | JSONField | optional |
| `price` | DecimalField |  |
| `stock` | IntegerField |  |
| `image` | ImageField | max_length=100, optional |
| `is_active` | BooleanField |  |

**Properties:**

- `is_low_stock`

### `Warehouse`

Physical or logical warehouse / storage location.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=100 |
| `code` | CharField | max_length=20, optional |
| `address` | TextField | optional |
| `is_active` | BooleanField |  |
| `is_default` | BooleanField |  |
| `sort_order` | PositiveIntegerField |  |

### `StockLevel`

Denormalised stock count per product-warehouse pair.

| Field | Type | Details |
|-------|------|---------|
| `product` | ForeignKey | → `inventory.Product`, on_delete=CASCADE |
| `warehouse` | ForeignKey | → `inventory.Warehouse`, on_delete=CASCADE |
| `quantity` | IntegerField |  |

### `StockMovement`

Audit trail for every stock change.

| Field | Type | Details |
|-------|------|---------|
| `product` | ForeignKey | → `inventory.Product`, on_delete=CASCADE |
| `warehouse` | ForeignKey | → `inventory.Warehouse`, on_delete=SET_NULL, optional |
| `movement_type` | CharField | max_length=20, choices: in, out, adjustment, transfer, return, sale |
| `quantity` | IntegerField |  |
| `reference` | CharField | max_length=100, optional |
| `notes` | TextField | optional |

### `StockAlert`

Alert when a product falls below its low-stock threshold.

| Field | Type | Details |
|-------|------|---------|
| `product` | ForeignKey | → `inventory.Product`, on_delete=CASCADE |
| `warehouse` | ForeignKey | → `inventory.Warehouse`, on_delete=SET_NULL, optional |
| `current_stock` | IntegerField |  |
| `threshold` | IntegerField |  |
| `status` | CharField | max_length=20, choices: active, acknowledged, resolved |
| `acknowledged_at` | DateTimeField | optional |
| `resolved_at` | DateTimeField | optional |

## Cross-Module Relationships

| From | Field | To | on_delete | Nullable |
|------|-------|----|-----------|----------|
| `Category` | `tax_class` | `configuration.TaxClass` | SET_NULL | Yes |
| `Product` | `tax_class` | `configuration.TaxClass` | SET_NULL | Yes |
| `ProductVariant` | `product` | `inventory.Product` | CASCADE | No |
| `StockLevel` | `product` | `inventory.Product` | CASCADE | No |
| `StockLevel` | `warehouse` | `inventory.Warehouse` | CASCADE | No |
| `StockMovement` | `product` | `inventory.Product` | CASCADE | No |
| `StockMovement` | `warehouse` | `inventory.Warehouse` | SET_NULL | Yes |
| `StockAlert` | `product` | `inventory.Product` | CASCADE | No |
| `StockAlert` | `warehouse` | `inventory.Warehouse` | SET_NULL | Yes |

## URL Endpoints

Base path: `/m/inventory/`

| Path | Name | Method |
|------|------|--------|
| `(root)` | `dashboard` | GET |
| `products/` | `products_list` | GET |
| `products/add/` | `product_add` | GET/POST |
| `products/<uuid:pk>/edit/` | `product_edit` | GET |
| `products/<uuid:pk>/delete/` | `product_delete` | GET/POST |
| `products/<uuid:pk>/toggle/` | `product_toggle_status` | GET |
| `products/bulk/` | `products_bulk_action` | GET/POST |
| `products/import/` | `products_import` | GET/POST |
| `products/<uuid:product_id>/barcode/` | `generate_barcode` | GET |
| `categories/` | `categories_index` | GET |
| `categories/add/` | `category_add` | GET/POST |
| `categories/<uuid:pk>/edit/` | `category_edit` | GET |
| `categories/<uuid:pk>/delete/` | `category_delete` | GET/POST |
| `categories/<uuid:pk>/toggle/` | `category_toggle_status` | GET |
| `categories/bulk/` | `categories_bulk_action` | GET/POST |
| `categories/import/` | `categories_import` | GET/POST |
| `reports/` | `reports` | GET |
| `settings/` | `settings` | GET |

## Permissions

| Permission | Description |
|------------|-------------|
| `inventory.view_product` | View Product |
| `inventory.add_product` | Add Product |
| `inventory.change_product` | Change Product |
| `inventory.delete_product` | Delete Product |
| `inventory.view_category` | View Category |
| `inventory.add_category` | Add Category |
| `inventory.change_category` | Change Category |
| `inventory.delete_category` | Delete Category |
| `inventory.view_warehouse` | View Warehouse |
| `inventory.add_warehouse` | Add Warehouse |
| `inventory.change_warehouse` | Change Warehouse |
| `inventory.view_stockmovement` | View Stockmovement |
| `inventory.add_stockmovement` | Add Stockmovement |
| `inventory.view_reports` | View Reports |
| `inventory.manage_settings` | Manage Settings |

**Role assignments:**

- **admin**: All permissions
- **manager**: `add_category`, `add_product`, `add_stockmovement`, `add_warehouse`, `change_category`, `change_product`, `change_warehouse`, `view_category` (+4 more)
- **employee**: `add_product`, `view_category`, `view_product`, `view_stockmovement`, `view_warehouse`

## Navigation

| View | Icon | ID | Fullpage |
|------|------|----|----------|
| Dashboard | `speedometer-outline` | `dashboard` | No |
| Products | `storefront-outline` | `products` | No |
| Categories | `pricetags-outline` | `categories` | No |
| Reports | `bar-chart-outline` | `reports` | No |
| Settings | `settings-outline` | `settings` | No |

## AI Tools

Tools available for the AI assistant:

### `list_products`

List products with optional filters. Returns name, SKU, price, stock, category.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search` | string | No | Search by name or SKU |
| `category_id` | string | No | Filter by category ID |
| `low_stock` | boolean | No | Only show products below low stock threshold |
| `limit` | integer | No | Max results (default 20) |

### `get_product`

Get detailed info for a specific product by ID or SKU.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | No | Product ID |
| `sku` | string | No | Product SKU |

### `create_product`

Create a new product in inventory.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Product name |
| `sku` | string | No | SKU code |
| `price` | string | Yes | Sale price |
| `cost` | string | No | Cost price |
| `description` | string | No | Product description |
| `stock` | integer | No | Initial stock quantity |
| `low_stock_threshold` | integer | No | Low stock alert threshold |
| `category_ids` | array | No | Category IDs to assign |
| `category_names` | array | No | Category names to assign (alternative to category_ids, matched case-insensitive) |

### `update_product`

Update an existing product's fields.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | Yes | Product ID to update |
| `name` | string | No | New name |
| `price` | string | No | New price |
| `cost` | string | No | New cost |
| `description` | string | No | New description |
| `stock` | integer | No | New stock quantity |
| `low_stock_threshold` | integer | No | New threshold |

### `list_categories`

List product categories.

### `create_category`

Create a new product category.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Category name |
| `icon` | string | No | Icon name (ionicon) |
| `color` | string | No | Hex color code |

### `adjust_stock`

Create a stock adjustment for a product (increase or decrease).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | Yes | Product ID |
| `quantity` | integer | Yes | Quantity to adjust (positive=add, negative=subtract) |
| `reason` | string | No | Reason for adjustment |

### `bulk_adjust_stock`

Adjust stock for multiple products at once (e.g., from a delivery note/albarán). Provide a list of items with product reference (name, SKU, or barcode) and quantity received.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `items` | array | Yes | List of products and quantities to adjust |
| `reason` | string | Yes | Reason for adjustment (e.g., 'Delivery note #12345') |

### `get_stock_alerts`

Get products that are below their low stock threshold.

### `set_product_allergens`

Set allergens for a product. Uses EU standard 14 allergens (RD 126/2015): gluten, crustaceans, eggs, fish, peanuts, soy, dairy, nuts, celery, mustard, sesame, sulphites, lupin, molluscs.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product_id` | string | Yes | Product ID |
| `allergens` | array | Yes | List of allergen codes (e.g. ['gluten', 'dairy', 'eggs']). Pass empty list to clear. |

## File Structure

```
CHANGELOG.md
README.md
__init__.py
admin.py
ai_tools.py
apps.py
barcode_utils.py
context_processors.py
fixtures/
  initial_data.json
forms.py
locale/
  README_I18N.md
  en/
    LC_MESSAGES/
      django.po
  es/
    LC_MESSAGES/
      django.po
management/
  __init__.py
  commands/
    __init__.py
    populate_ean13.py
migrations/
  0001_initial.py
  0002_add_allergens_to_product.py
  0003_category_code_product_source.py
  __init__.py
models.py
module.py
static/
  icons/
    icon.svg
    ion/
  products/
    css/
      products.css
templates/
  inventory/
    pages/
      categories.html
      category_add.html
      category_edit.html
      index.html
      product_add.html
      product_edit.html
      products.html
      reports.html
      settings.html
    partials/
      categories_content.html
      categories_list.html
      category_add_content.html
      category_edit_content.html
      dashboard_content.html
      panel_category_add.html
      panel_category_edit.html
      panel_product_add.html
      panel_product_edit.html
      product_add_content.html
      product_edit_content.html
      products_content.html
      products_list.html
      reports_content.html
      settings_content.html
tests/
  __init__.py
  test_e2e.py
  test_models.py
  test_views.py
urls.py
views.py
```
