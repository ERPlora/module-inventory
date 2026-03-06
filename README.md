# Inventory Module

Comprehensive product and inventory management for ERPlora Hub.

## Features

- Full CRUD for products and categories
- Product types: physical (affects stock) and service
- Product variants with custom attributes (color, size, weight)
- Multi-warehouse stock management with stock levels per product-warehouse pair
- Stock movements audit trail (in, out, adjustment, transfer, return, sale)
- Low stock alerts with configurable thresholds per product
- Tax class inheritance: Product > Category > StoreConfig default
- SKU auto-generation and EAN-13 barcode support
- Barcode generation (Code128/EAN13) and native print support
- Image upload for products and categories with letter fallback
- CSV and Excel import/export for products and categories
- Bulk actions (activate, deactivate, delete)
- Profit margin calculations (cost vs price)
- Search, filtering, and pagination

## Installation

This module is installed automatically via the ERPlora Marketplace.

## Configuration

Access settings via: **Menu > Inventory > Settings**

Settings include:
- Allow negative stock
- Low stock alerts toggle
- Auto-generate SKU toggle
- Barcode generation toggle

## Usage

Access via: **Menu > Inventory**

### Views

| View | URL | Description |
|------|-----|-------------|
| Dashboard | `/m/inventory/` | Overview of inventory metrics and stock alerts |
| Products | `/m/inventory/products/` | List, create, edit, and delete products |
| Product Add | `/m/inventory/products/add/` | Create new product |
| Product Edit | `/m/inventory/products/<id>/edit/` | Edit existing product |
| Categories | `/m/inventory/categories/` | Manage product categories |
| Category Add | `/m/inventory/categories/add/` | Create new category |
| Reports | `/m/inventory/reports/` | Inventory reports |
| Settings | `/m/inventory/settings/` | Module configuration |

### Actions

| Action | URL | Method |
|--------|-----|--------|
| Product Toggle Status | `/m/inventory/products/<id>/toggle/` | POST |
| Products Bulk Action | `/m/inventory/products/bulk/` | POST |
| Products Import | `/m/inventory/products/import/` | POST |
| Generate Barcode | `/m/inventory/products/<id>/barcode/` | GET |
| Category Toggle Status | `/m/inventory/categories/<id>/toggle/` | POST |
| Categories Bulk Action | `/m/inventory/categories/bulk/` | POST |
| Categories Import | `/m/inventory/categories/import/` | POST |

## Models

| Model | Description |
|-------|-------------|
| `InventorySettings` | Per-hub settings (negative stock, low stock alerts, auto SKU, barcode) |
| `Category` | Product category with icon, color, image, tax class, sort order |
| `Product` | Product with SKU, EAN-13, price, cost, stock, type (physical/service), tax class |
| `ProductVariant` | Variant of a product with custom attributes, separate SKU, price, and stock |
| `Warehouse` | Physical or logical storage location with code and default flag |
| `StockLevel` | Denormalized stock count per product-warehouse pair |
| `StockMovement` | Audit trail for every stock change (in, out, adjustment, transfer, return, sale) |
| `StockAlert` | Alert when product falls below low-stock threshold (active, acknowledged, resolved) |

## Permissions

| Permission | Description |
|------------|-------------|
| `inventory.view_product` | View products |
| `inventory.add_product` | Create products |
| `inventory.change_product` | Edit products |
| `inventory.delete_product` | Delete products |
| `inventory.view_category` | View categories |
| `inventory.add_category` | Create categories |
| `inventory.change_category` | Edit categories |
| `inventory.delete_category` | Delete categories |
| `inventory.view_warehouse` | View warehouses |
| `inventory.add_warehouse` | Create warehouses |
| `inventory.change_warehouse` | Edit warehouses |
| `inventory.view_stockmovement` | View stock movements |
| `inventory.add_stockmovement` | Create stock movements |
| `inventory.view_reports` | View reports |
| `inventory.manage_settings` | Manage module settings |

## Integration with Other Modules

| Module | Integration |
|--------|-------------|
| `sales` | Stock deduction on sale (StockMovement type=sale) |
| `customers` | Customer assignment |
| `invoicing` | Invoice generation from sales |
| `cash_register` | Cash session management |
| `configuration` | TaxClass inheritance for products and categories |

## Dependencies

None

## License

MIT

## Author

ERPlora Team - support@erplora.com
