"""AI tools for the Inventory module."""
from assistant.tools import AssistantTool, register_tool


@register_tool
class ListProducts(AssistantTool):
    name = "list_products"
    description = "List products with optional filters. Returns name, SKU, price, stock, category."
    module_id = "inventory"
    required_permission = "inventory.view_product"
    parameters = {
        "type": "object",
        "properties": {
            "search": {"type": "string", "description": "Search by name or SKU"},
            "category_id": {"type": "string", "description": "Filter by category ID"},
            "low_stock": {"type": "boolean", "description": "Only show products below low stock threshold"},
            "limit": {"type": "integer", "description": "Max results (default 20)"},
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
    description = "Get detailed info for a specific product by ID or SKU."
    module_id = "inventory"
    required_permission = "inventory.view_product"
    parameters = {
        "type": "object",
        "properties": {
            "product_id": {"type": "string", "description": "Product ID"},
            "sku": {"type": "string", "description": "Product SKU"},
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
    description = "Create a new product in inventory."
    module_id = "inventory"
    required_permission = "inventory.change_product"
    requires_confirmation = True
    examples = [
        {"name": "Champú Pro 500ml", "price": "12.50", "stock": 50, "sku": "CHAMP-001"},
        {"name": "Tinte Rubio Ceniza", "price": "8.90", "cost": "4.50", "stock": 30},
    ]
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Product name"},
            "sku": {"type": "string", "description": "SKU code"},
            "price": {"type": "string", "description": "Sale price"},
            "cost": {"type": "string", "description": "Cost price"},
            "description": {"type": "string", "description": "Product description"},
            "stock": {"type": "integer", "description": "Initial stock quantity"},
            "low_stock_threshold": {"type": "integer", "description": "Low stock alert threshold"},
            "category_ids": {"type": "array", "items": {"type": "string"}, "description": "Category IDs to assign"},
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
            cost=Decimal(args['cost']) if args.get('cost') else None,
            description=args.get('description', ''),
            stock=args.get('stock', 0),
            low_stock_threshold=args.get('low_stock_threshold', 0),
        )
        if args.get('category_ids'):
            cats = Category.objects.filter(id__in=args['category_ids'])
            p.categories.set(cats)
        return {"id": str(p.id), "name": p.name, "sku": p.sku, "created": True}


@register_tool
class UpdateProduct(AssistantTool):
    name = "update_product"
    description = "Update an existing product's fields."
    module_id = "inventory"
    required_permission = "inventory.change_product"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "product_id": {"type": "string", "description": "Product ID to update"},
            "name": {"type": "string", "description": "New name"},
            "price": {"type": "string", "description": "New price"},
            "cost": {"type": "string", "description": "New cost"},
            "description": {"type": "string", "description": "New description"},
            "stock": {"type": "integer", "description": "New stock quantity"},
            "low_stock_threshold": {"type": "integer", "description": "New threshold"},
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
    description = "List product categories."
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
    description = "Create a new product category."
    module_id = "inventory"
    required_permission = "inventory.change_product"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Category name"},
            "icon": {"type": "string", "description": "Icon name (ionicon)"},
            "color": {"type": "string", "description": "Hex color code"},
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
    description = "Create a stock adjustment for a product (increase or decrease)."
    module_id = "inventory"
    required_permission = "inventory.change_product"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "product_id": {"type": "string", "description": "Product ID"},
            "quantity": {"type": "integer", "description": "Quantity to adjust (positive=add, negative=subtract)"},
            "reason": {"type": "string", "description": "Reason for adjustment"},
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
        "Adjust stock for multiple products at once (e.g., from a delivery "
        "note/albarán). Provide a list of items with product reference "
        "(name, SKU, or barcode) and quantity received."
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
                            "description": "Product name, SKU, or barcode",
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "Quantity to add (positive) or subtract (negative)",
                        },
                    },
                    "required": ["reference", "quantity"],
                },
                "description": "List of products and quantities to adjust",
            },
            "reason": {
                "type": "string",
                "description": "Reason for adjustment (e.g., 'Delivery note #12345')",
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
    description = "Get products that are below their low stock threshold."
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
