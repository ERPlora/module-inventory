# Changelog

All notable changes to the Inventory module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-25

### Added

- Initial release of Inventory module
- **Core Features**
  - Product catalog management
  - Category organization
  - Stock level tracking
  - Low stock alerts
  - Barcode/SKU support
  - Product images

- **Models**
  - `Product`: Product catalog with pricing and stock
  - `Category`: Product categories (hierarchical)
  - `StockMovement`: Stock in/out tracking
  - `InventoryConfig`: Module configuration

- **Views**
  - Product list with search and filters
  - Product detail view
  - Product creation/edit form
  - Category management
  - Stock adjustment

- **Internationalization**
  - English translations (base)
  - Spanish translations

### Technical Details

- Automatic stock deduction on sales
- Stock history tracking
- Integration with Sales module
- Integration with Invoicing module

---

## [Unreleased]

### Planned

- Batch/lot tracking
- Expiry date management
- Multiple warehouses/locations
- Stock transfers
- Inventory valuation (FIFO, LIFO, Average)
- Purchase orders
- Supplier management
- Barcode printing
