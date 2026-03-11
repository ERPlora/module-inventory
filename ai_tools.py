"""AI tools for the Inventory module."""
from assistant.tools import AssistantTool, register_tool


@register_tool
class ListProducts(AssistantTool):
    name = "list_products"
    description = (
        "Use this to browse or search the product catalog. "
        "Returns product name, SKU, price, cost, current stock, low-stock threshold, and product type. "
        "Read-only — no side effects. "
        "For full details (description, allergens, EAN13, categories), use get_product. "
        "Example triggers: 'what products do we have?', 'search for champú', 'show low stock items'"
    )
    module_id = "inventory"
    required_permission = "inventory.view_product"
    parameters = {
        "type": "object",
        "properties": {
            "search": {
                "type": "string",
                "description": "Filter by product name or SKU (case-insensitive partial match).",
            },
            "category_id": {
                "type": "string",
                "description": "Filter by category ID. Use list_categories to get category IDs.",
            },
            "low_stock": {
                "type": "boolean",
                "description": "Set to true to return only products at or below their low-stock threshold. Omit or set false for all products.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of products to return. Default is 20.",
            },
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from inventory.models import Product
        qs = Product.objects.select_related('tax_class').all()
        if args.get('search'):
            qs = qs.filter(name__icontains=args['search']) | qs.filter(sku__icontains=args['search'])
        if args.get('category_id'):
            qs = qs.filter(categories__id=args['category_id'])
        if args.get('low_stock'):
            from django.db.models import F
            qs = qs.filter(stock__lte=F('low_stock_threshold'))
        limit = args.get('limit', 20)
        products = qs[:limit]
        return {
            "products": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "sku": p.sku,
                    "price": str(p.price),
                    "cost": str(p.cost) if p.cost else None,
                    "stock": p.stock,
                    "low_stock_threshold": p.low_stock_threshold,
                    "product_type": p.product_type,
                }
                for p in products
            ],
            "total": qs.count(),
        }


@register_tool
class GetProduct(AssistantTool):
    name = "get_product"
    description = (
        "Use this to get the complete details of a single product: name, SKU, EAN13 barcode, "
        "description, price, cost, stock level, low-stock threshold, product type, categories, "
        "tax class, and allergens. "
        "Read-only — no side effects. "
        "Provide either product_id (UUID) or sku. Use list_products to find an ID or SKU first."
    )
    module_id = "inventory"
    required_permission = "inventory.view_product"
    parameters = {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "Internal UUID of the product.",
            },
            "sku": {
                "type": "string",
                "description": "Product SKU code (exact match).",
            },
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from inventory.models import Product
        if args.get('product_id'):
            p = Product.objects.get(id=args['product_id'])
        elif args.get('sku'):
            p = Product.objects.get(sku=args['sku'])
        else:
            return {"error": "Provide product_id or sku"}
        return {
            "id": str(p.id),
            "name": p.name,
            "sku": p.sku,
            "ean13": p.ean13,
            "description": p.description,
            "price": str(p.price),
            "cost": str(p.cost) if p.cost else None,
            "stock": p.stock,
            "low_stock_threshold": p.low_stock_threshold,
            "product_type": p.product_type,
            "categories": [{"id": str(c.id), "name": c.name} for c in p.categories.all()],
            "tax_class": p.tax_class.name if p.tax_class else None,
        }


@register_tool
class CreateProduct(AssistantTool):
    name = "create_product"
    description = (
        "Use this to add a new product to the inventory catalog. "
        "SIDE EFFECT: creates a new product record. Requires confirmation. "
        "Price is required; SKU is optional but recommended for stock tracking. "
        "Categories can be specified by ID (preferred) or by name (case-insensitive lookup). "
        "Use list_categories to find valid category IDs or names before calling this."
    )
    module_id = "inventory"
    required_permission = "inventory.change_product"
    requires_confirmation = True
    examples = [
        {"name": "Champú Pro 500ml", "price": "12.50", "stock": 50, "sku": "CHAMP-001", "category_names": ["Champús"]},
        {"name": "Tinte Rubio Ceniza", "price": "8.90", "cost": "4.50", "stock": 30, "category_names": ["Tintes"]},
    ]
    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Product display name.",
            },
            "sku": {
                "type": "string",
                "description": "Unique SKU code for stock tracking. Optional but recommended.",
            },
            "price": {
                "type": "string",
                "description": "Sale price as a decimal string (e.g., '12.50'). Required.",
            },
            "cost": {
                "type": "string",
                "description": "Purchase/cost price as a decimal string (e.g., '6.00'). Used for margin calculations.",
            },
            "description": {
                "type": "string",
                "description": "Optional product description or notes.",
            },
            "stock": {
                "type": "integer",
                "description": "Initial stock quantity. Defaults to 0.",
            },
            "low_stock_threshold": {
                "type": "integer",
                "description": "Stock level at which a low-stock alert is triggered. Defaults to 0 (no alert).",
            },
            "category_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of category UUIDs to assign. Preferred over category_names.",
            },
            "category_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of category names to assign (case-insensitive lookup). Use when you don't have IDs.",
            },
        },
        "required": ["name", "price"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from decimal import Decimal
        from inventory.models import Product, Category
        p = Product.objects.create(
            name=args['name'],
            sku=args.get('sku', ''),
            price=Decimal(args['price']),
            cost=Decimal(args['cost']) if args.get('cost') else Decimal('0.00'),
            description=args.get('description', ''),
            stock=args.get('stock', 0),
            low_stock_threshold=args.get('low_stock_threshold', 0),
        )
        if args.get('category_ids'):
            cats = Category.objects.filter(id__in=args['category_ids'])
            p.categories.set(cats)
        elif args.get('category_names'):
            cats = Category.objects.filter(name__in=args['category_names'])
            if not cats.exists():
                # Try case-insensitive match
                for name in args['category_names']:
                    cat = Category.objects.filter(name__iexact=name).first()
                    if cat:
                        p.categories.add(cat)
            else:
                p.categories.set(cats)
        return {"id": str(p.id), "name": p.name, "sku": p.sku, "created": True}


@register_tool
class UpdateProduct(AssistantTool):
    name = "update_product"
    description = (
        "Use this to modify an existing product's fields (name, price, cost, description, stock, or low-stock threshold). "
        "SIDE EFFECT: updates the product record. Requires confirmation. "
        "Only the fields you provide are changed; omitted fields remain unchanged. "
        "Use get_product or list_products to find the product_id before calling this. "
        "To adjust stock with a reason/audit trail, prefer adjust_stock instead of setting stock directly here."
    )
    module_id = "inventory"
    required_permission = "inventory.change_product"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "UUID of the product to update. Required.",
            },
            "name": {
                "type": "string",
                "description": "New product name.",
            },
            "price": {
                "type": "string",
                "description": "New sale price as a decimal string (e.g., '15.00').",
            },
            "cost": {
                "type": "string",
                "description": "New cost price as a decimal string.",
            },
            "description": {
                "type": "string",
                "description": "New product description.",
            },
            "stock": {
                "type": "integer",
                "description": "Override the stock quantity directly. Prefer adjust_stock for audited adjustments.",
            },
            "low_stock_threshold": {
                "type": "integer",
                "description": "New low-stock alert threshold. Set to 0 to disable the alert.",
            },
        },
        "required": ["product_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from decimal import Decimal
        from inventory.models import Product
        p = Product.objects.get(id=args['product_id'])
        if 'name' in args:
            p.name = args['name']
        if 'price' in args:
            p.price = Decimal(args['price'])
        if 'cost' in args:
            p.cost = Decimal(args['cost'])
        if 'description' in args:
            p.description = args['description']
        if 'stock' in args:
            p.stock = args['stock']
        if 'low_stock_threshold' in args:
            p.low_stock_threshold = args['low_stock_threshold']
        p.save()
        return {"id": str(p.id), "name": p.name, "updated": True}


@register_tool
class ListCategories(AssistantTool):
    name = "list_categories"
    description = (
        "Use this to see all product categories with their IDs, names, slugs, and product counts. "
        "Read-only — no side effects. "
        "Call this before create_product or list_products when you need category IDs or names."
    )
    module_id = "inventory"
    required_permission = "inventory.view_product"
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from inventory.models import Category
        cats = Category.objects.all()
        return {
            "categories": [
                {"id": str(c.id), "name": c.name, "slug": c.slug, "product_count": c.product_count}
                for c in cats
            ]
        }


@register_tool
class CreateCategory(AssistantTool):
    name = "create_category"
    description = (
        "Use this to create a new product category. "
        "SIDE EFFECT: creates a new category record. Requires confirmation. "
        "Call list_categories first to avoid duplicates. "
        "The icon should be a valid ionicon name (e.g., 'cube-outline', 'pricetag-outline')."
    )
    module_id = "inventory"
    required_permission = "inventory.change_product"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Category name (e.g., 'Champús', 'Bebidas', 'Postres').",
            },
            "icon": {
                "type": "string",
                "description": "Ionicon name for visual identification (e.g., 'cube-outline', 'leaf-outline'). Optional.",
            },
            "color": {
                "type": "string",
                "description": "Hex color code for visual identification (e.g., '#3B82F6'). Optional.",
            },
        },
        "required": ["name"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from inventory.models import Category
        from django.utils.text import slugify
        c = Category.objects.create(
            name=args['name'],
            slug=slugify(args['name']),
            icon=args.get('icon', ''),
            color=args.get('color', ''),
        )
        return {"id": str(c.id), "name": c.name, "created": True}


@register_tool
class AdjustStock(AssistantTool):
    name = "adjust_stock"
    description = (
        "Use this to increase or decrease the stock of a single product, with a reason recorded in the audit log. "
        "SIDE EFFECT: creates a StockMovement record and updates product.stock. Requires confirmation. "
        "Use positive quantity to add stock (e.g., receiving a delivery), negative to subtract (e.g., breakage, correction). "
        "For adjusting multiple products at once, use bulk_adjust_stock. "
        "Example triggers: 'add 24 units of product X', 'remove 5 units due to breakage'"
    )
    module_id = "inventory"
    required_permission = "inventory.change_product"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "UUID of the product to adjust. Use list_products or get_product to find it.",
            },
            "quantity": {
                "type": "integer",
                "description": "Quantity change: positive to add stock (e.g., 24), negative to subtract (e.g., -5).",
            },
            "reason": {
                "type": "string",
                "description": "Human-readable reason recorded in the stock movement log (e.g., 'Delivery note #1234', 'Breakage', 'Inventory count correction').",
            },
        },
        "required": ["product_id", "quantity"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from inventory.models import Product, StockMovement
        p = Product.objects.get(id=args['product_id'])
        qty = args['quantity']
        movement_type = 'in' if qty > 0 else 'adjustment'
        StockMovement.objects.create(
            product=p,
            movement_type=movement_type,
            quantity=abs(qty),
            reference=args.get('reason', 'AI assistant adjustment'),
        )
        p.stock += qty
        p.save(update_fields=['stock'])
        return {"product": p.name, "new_stock": p.stock, "adjusted_by": qty}


@register_tool
class BulkAdjustStock(AssistantTool):
    name = "bulk_adjust_stock"
    description = (
        "Use this to adjust stock for multiple products in a single operation — ideal for processing a delivery note (albarán). "
        "Each item can be identified by SKU, EAN13 barcode, or product name (exact or partial). "
        "SIDE EFFECT: creates StockMovement records and updates stock for each matched product. Requires confirmation. "
        "Returns a list of adjusted products and any references that could not be matched. "
        "For single-product adjustments, use adjust_stock instead."
    )
    module_id = "inventory"
    required_permission = "inventory.change_product"
    requires_confirmation = True
    examples = [
        {"items": [{"reference": "CHAMP-001", "quantity": 24}, {"reference": "Tinte Rubio", "quantity": 12}], "reason": "Delivery note #1234"},
    ]
    parameters = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "reference": {
                            "type": "string",
                            "description": "Product identifier: SKU (exact), EAN13 barcode (exact), or product name (case-insensitive, partial match as fallback).",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "Quantity to add (positive) or subtract (negative).",
                        },
                    },
                    "required": ["reference", "quantity"],
                },
                "description": "List of products and quantities to adjust.",
            },
            "reason": {
                "type": "string",
                "description": "Reason applied to all movements in this batch (e.g., 'Delivery note #12345', 'Monthly inventory count').",
            },
        },
        "required": ["items", "reason"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from inventory.models import Product, StockMovement

        items = args.get('items', [])
        reason = args.get('reason', 'Bulk adjustment')
        adjusted = []
        not_found = []

        for item in items:
            ref = item.get('reference', '').strip()
            qty = item.get('quantity', 0)
            if not ref or not qty:
                not_found.append({"reference": ref, "reason": "Empty reference or zero quantity"})
                continue

            # Search by SKU (exact), EAN13 (exact), then name (case-insensitive contains)
            product = (
                Product.objects.filter(sku__iexact=ref).first()
                or Product.objects.filter(ean13=ref).first()
                or Product.objects.filter(name__iexact=ref).first()
                or Product.objects.filter(name__icontains=ref).first()
            )

            if not product:
                not_found.append({"reference": ref, "reason": "Product not found"})
                continue

            movement_type = 'in' if qty > 0 else 'adjustment'
            StockMovement.objects.create(
                product=product,
                movement_type=movement_type,
                quantity=abs(qty),
                reference=reason,
            )
            product.stock += qty
            product.save(update_fields=['stock'])
            adjusted.append({
                "reference": ref,
                "product_name": product.name,
                "sku": product.sku,
                "quantity": qty,
                "new_stock": product.stock,
            })

        return {
            "adjusted": adjusted,
            "not_found": not_found,
            "summary": f"{len(adjusted)} products adjusted, {len(not_found)} not found",
        }


@register_tool
class GetStockAlerts(AssistantTool):
    name = "get_stock_alerts"
    description = (
        "Use this to identify products that need restocking. "
        "Returns all products whose current stock is at or below their configured low-stock threshold. "
        "Only products with a threshold greater than 0 are included. "
        "Read-only — no side effects. "
        "Example triggers: 'what needs restocking?', 'show me low stock alerts', 'what products are running out?'"
    )
    module_id = "inventory"
    required_permission = "inventory.view_product"
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from django.db.models import F
        from inventory.models import Product
        low = Product.objects.filter(
            low_stock_threshold__gt=0,
            stock__lte=F('low_stock_threshold'),
        )
        return {
            "alerts": [
                {"name": p.name, "sku": p.sku, "stock": p.stock, "threshold": p.low_stock_threshold}
                for p in low[:50]
            ],
            "total": low.count(),
        }


@register_tool
class SetProductAllergens(AssistantTool):
    name = "set_product_allergens"
    description = (
        "Use this to set or update the allergen list for a product (EU standard 14 allergens per RD 126/2015). "
        "SIDE EFFECT: overwrites the product's allergen list. Requires confirmation. "
        "Pass an empty list to clear all allergens. "
        "Valid allergen codes: gluten, crustaceans, eggs, fish, peanuts, soy, dairy, nuts, "
        "celery, mustard, sesame, sulphites, lupin, molluscs. "
        "Invalid codes are silently ignored."
    )
    module_id = "inventory"
    required_permission = "inventory.change_product"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "UUID of the product to update.",
            },
            "allergens": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of allergen codes to set. Valid values: gluten, crustaceans, eggs, fish, "
                    "peanuts, soy, dairy, nuts, celery, mustard, sesame, sulphites, lupin, molluscs. "
                    "Pass an empty list [] to remove all allergens from the product."
                ),
            },
        },
        "required": ["product_id", "allergens"],
        "additionalProperties": False,
    }

    VALID_ALLERGENS = {
        'gluten', 'crustaceans', 'eggs', 'fish', 'peanuts', 'soy',
        'dairy', 'nuts', 'celery', 'mustard', 'sesame', 'sulphites',
        'lupin', 'molluscs',
    }

    def execute(self, args, request):
        from inventory.models import Product
        product = Product.objects.get(id=args['product_id'])
        allergens = [a for a in args['allergens'] if a in self.VALID_ALLERGENS]
        product.allergens = allergens
        product.save(update_fields=['allergens', 'updated_at'])
        return {
            "product": product.name,
            "allergens": allergens,
            "allergen_names": product.allergen_names,
            "updated": True,
        }


@register_tool
class ExportProductsCSV(AssistantTool):
    name = "export_products_csv"
    description = (
        "Use this to generate a downloadable CSV of the product catalog. "
        "Returns a download URL that the user can click to get the file. "
        "The CSV includes: name, SKU, price, cost, stock, categories, tax class, and active status. "
        "SIDE EFFECT: creates a file in the exports directory. "
        "Example triggers: 'export all products to Excel', 'download the product list'"
    )
    module_id = "inventory"
    required_permission = "inventory.view_product"
    parameters = {
        "type": "object",
        "properties": {
            "search": {
                "type": "string",
                "description": "Filter by product name or SKU (case-insensitive partial match).",
            },
            "category_id": {
                "type": "string",
                "description": "Filter by category ID to export only products in that category.",
            },
            "active_only": {
                "type": "boolean",
                "description": "If true (default), only active products are exported. Set to false to include inactive products.",
            },
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        import os
        import time
        from django.conf import settings
        from apps.core.services.export_service import generate_csv_string
        from inventory.models import Product

        qs = Product.objects.select_related('tax_class').all()
        if args.get('search'):
            from django.db.models import Q
            s = args['search']
            qs = qs.filter(Q(name__icontains=s) | Q(sku__icontains=s))
        if args.get('category_id'):
            qs = qs.filter(categories__id=args['category_id'])
        if args.get('active_only', True):
            qs = qs.filter(is_active=True)

        # Build data with custom fields
        data = []
        for p in qs:
            data.append({
                'name': p.name,
                'sku': p.sku,
                'price': str(p.price),
                'cost': str(p.cost) if p.cost else '',
                'stock': p.stock,
                'categories': ', '.join(c.name for c in p.categories.all()),
                'tax_class': p.tax_class.name if p.tax_class else '',
                'is_active': 'Yes' if p.is_active else 'No',
            })

        fields = ['name', 'sku', 'price', 'cost', 'stock', 'categories', 'tax_class', 'is_active']
        headers = ['Name', 'SKU', 'Price', 'Cost', 'Stock', 'Categories', 'Tax Class', 'Active']

        export_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
        os.makedirs(export_dir, exist_ok=True)
        filename = f'products_{int(time.time())}.csv'
        filepath = os.path.join(export_dir, filename)

        csv_content = generate_csv_string(data, fields=fields, headers=headers)
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write(csv_content)

        return {"download_url": f"/media/exports/{filename}", "count": len(data)}


@register_tool
class ImportProductsCSV(AssistantTool):
    name = "import_products_csv"
    description = (
        "Use this to bulk-import products from a CSV file that the user has uploaded. "
        "SIDE EFFECT: creates new product records. Requires confirmation. "
        "Expected CSV columns: Name (required), SKU, Price, Cost, Stock, Categories (comma-separated), Tax Class. "
        "Products with an SKU that already exists are skipped (not updated). "
        "Categories are matched by name (case-insensitive); unmatched categories are ignored. "
        "Returns counts of created, skipped, and error rows. "
        "Only use this when the user provides or uploads a CSV file — do not guess a file_path."
    )
    module_id = "inventory"
    required_permission = "inventory.change_product"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the uploaded CSV file on the server (provided by the file upload system).",
            },
        },
        "required": ["file_path"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        import csv
        import io
        from decimal import Decimal, InvalidOperation
        from inventory.models import Product, Category

        file_path = args['file_path']

        # Read the CSV file
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except FileNotFoundError:
            return {"error": f"File not found: {file_path}"}

        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)

        if not rows:
            return {"error": "CSV file is empty or has no data rows"}

        created = 0
        skipped = 0
        errors = []

        for i, row in enumerate(rows, start=2):
            name = row.get('Name', row.get('name', '')).strip()
            if not name:
                errors.append(f"Row {i}: missing product name")
                continue

            sku = row.get('SKU', row.get('sku', '')).strip()
            if sku and Product.objects.filter(sku=sku).exists():
                skipped += 1
                continue

            try:
                price = Decimal(row.get('Price', row.get('price', '0')).strip() or '0')
            except (InvalidOperation, ValueError):
                errors.append(f"Row {i}: invalid price")
                continue

            try:
                cost = Decimal(row.get('Cost', row.get('cost', '0')).strip() or '0')
            except (InvalidOperation, ValueError):
                cost = Decimal('0.00')

            try:
                stock = int(row.get('Stock', row.get('stock', '0')).strip() or '0')
            except (ValueError, TypeError):
                stock = 0

            product = Product.objects.create(
                name=name,
                sku=sku,
                price=price,
                cost=cost,
                stock=stock,
            )

            # Map categories by name
            cat_str = row.get('Categories', row.get('categories', '')).strip()
            if cat_str:
                cat_names = [c.strip() for c in cat_str.split(',') if c.strip()]
                for cat_name in cat_names:
                    cat = Category.objects.filter(name__iexact=cat_name).first()
                    if cat:
                        product.categories.add(cat)

            created += 1

        return {
            "created": created,
            "skipped": skipped,
            "errors": errors[:20],
            "total_rows": len(rows),
        }
