"""
AI context for the Inventory module.
Loaded into the assistant system prompt when this module's tools are active.
"""

CONTEXT = """
## Module Knowledge: Inventory

### Models
**Category** — Product category for grouping and POS display.
- `name`, `slug`, `icon` (djicons name), `color` (hex), `image`
- `tax_class` → configuration.TaxClass (default tax for products in this category)
- `sort_order`, `is_active`
- `code`: blueprint seed identifier (e.g. 'bebidas', 'entrantes')

**Product** — Item in the catalogue.
- `name`, `sku` (auto-generated if enabled), `ean13` (barcode)
- `product_type`: physical (affects stock) | service (no stock)
- `source`: user | blueprint | import
- `unit_of_measure`: unit | kg | g | l | ml | m | cm
- `sold_by_weight`: True → requires quantity input at POS
- `price` (selling price), `cost` (purchase cost)
- `stock` (current quantity), `low_stock_threshold` (default 10)
- `categories` (M2M → Category)
- `tax_class` → TaxClass (overrides category tax class if set)
- `allergens` (JSONField): list of codes from EU 14 allergens
  Codes: gluten, crustaceans, eggs, fish, peanuts, soy, dairy, nuts,
         celery, mustard, sesame, sulphites, lupin, molluscs
- `is_active`

**Tax class inheritance**: Product.tax_class → Category.tax_class → StoreConfig.default_tax_class

**ProductVariant** — Variant of a product (colour, size, weight).
- `product` → Product (FK), `name`, `sku`, `price`, `stock`
- `attributes` (JSONField): e.g. {"color": "red", "size": "XL"}

**Warehouse** — Physical or logical storage location.
- `name`, `code` (e.g. WH-01), `is_default`

**StockLevel** — Stock per product-warehouse pair.
- `product` → Product, `warehouse` → Warehouse, `quantity`

**StockMovement** — Audit trail for every stock change.
- `movement_type`: in | out | adjustment | transfer | return | sale
- `quantity` (positive=in, negative=out), `reference` (sale number, PO, etc.)

**StockAlert** — Alert when product falls below threshold.
- `status`: active | acknowledged | resolved

### Key flows
1. Create product → assign categories → set price → optionally set tax_class
2. Stock adjustment: create StockMovement (type=adjustment) → updates Product.stock
3. Stock in (purchase): movement_type=in → increases stock
4. Sale: movement_type=sale → decreases stock (auto on sale complete)
5. Low stock: alert created when stock ≤ low_stock_threshold
6. Blueprint products: source=blueprint, come with images from CDN

### Settings (InventorySettings)
- `allow_negative_stock`: allow stock < 0
- `low_stock_alert_enabled`
- `auto_generate_sku`: auto-create SKU on save
- `barcode_enabled`

### Relationships
- Product → SaleItem (sales_sale_item.product_id)
- Product → OrderItem (orders_order_item.product_id)
- Product → StockLevel (per warehouse)
- Product → StockMovement (audit trail)
- Category → Product (M2M)
"""
