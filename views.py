"""
Inventory Module Views

Products, categories, dashboard, reports, settings.
Follows the datatable pattern (search, sort, filter, pagination, export, import, bulk).
"""
import csv
import io
from decimal import Decimal

from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum, F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render as django_render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.accounts.decorators import login_required
from apps.core.htmx import htmx_view
from apps.core.services import export_to_csv, export_to_excel
from apps.core.services.import_service import parse_import_file, ImportResult
from apps.modules_runtime.navigation import with_module_nav
from apps.configuration.models import HubConfig, StoreConfig, TaxClass

from .models import Category, Product, InventorySettings


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PRODUCT_SORT_FIELDS = {
    'name': 'name',
    'sku': 'sku',
    'price': 'price',
    'stock': 'stock',
    'created_at': 'created_at',
}

CATEGORY_SORT_FIELDS = {
    'name': 'name',
    'sort_order': 'sort_order',
}

PER_PAGE_CHOICES = [10, 25, 50, 100]


# ---------------------------------------------------------------------------
# Products — Helpers
# ---------------------------------------------------------------------------

def _build_products_context(hub_id, per_page=10):
    """Build context for the products list after mutations."""
    products = Product.objects.filter(
        hub_id=hub_id, is_deleted=False,
    ).prefetch_related('categories').order_by('name')
    paginator = Paginator(products, per_page)
    page_obj = paginator.get_page(1)
    categories_list = Category.objects.filter(
        hub_id=hub_id, is_deleted=False, is_active=True,
    ).order_by('sort_order', 'name')
    return {
        'products': page_obj,
        'page_obj': page_obj,
        'search_query': '',
        'sort_field': 'name',
        'sort_dir': 'asc',
        'category_filter': '',
        'status_filter': '',
        'categories_list': categories_list,
        'current_view': 'table',
        'per_page': per_page,
    }


def _render_products_list(request, hub_id, per_page=10):
    """Render the products list partial after a mutation."""
    context = _build_products_context(hub_id, per_page)
    return django_render(request, 'inventory/partials/products_list.html', context)


# ---------------------------------------------------------------------------
# Categories — Helpers
# ---------------------------------------------------------------------------

def _build_categories_context(hub_id, per_page=10):
    """Build context for the categories list after mutations."""
    categories = Category.objects.filter(
        hub_id=hub_id, is_deleted=False,
    ).order_by('sort_order', 'name')
    paginator = Paginator(categories, per_page)
    page_obj = paginator.get_page(1)
    return {
        'categories': page_obj,
        'page_obj': page_obj,
        'search_query': '',
        'sort_field': 'sort_order',
        'sort_dir': 'asc',
        'status_filter': '',
        'current_view': 'table',
        'per_page': per_page,
    }


def _render_categories_list(request, hub_id, per_page=10):
    """Render the categories list partial after a mutation."""
    context = _build_categories_context(hub_id, per_page)
    return django_render(request, 'inventory/partials/categories_list.html', context)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
@with_module_nav('inventory', 'dashboard')
@htmx_view('inventory/pages/index.html', 'inventory/partials/dashboard_content.html')
def dashboard(request):
    """Main inventory dashboard with statistics."""
    hub_id = request.session.get('hub_id')
    currency = HubConfig.get_value('currency', 'EUR')

    products = Product.objects.filter(hub_id=hub_id, is_deleted=False, is_active=True)

    total_products = products.count()
    products_in_stock = products.filter(stock__gt=0).count()
    products_low_stock = products.filter(stock__lte=F('low_stock_threshold')).count()
    total_inventory_value = products.aggregate(
        total=Sum(F('stock') * F('price'))
    )['total'] or 0

    categories = Category.objects.filter(
        hub_id=hub_id, is_deleted=False, is_active=True,
    ).order_by('sort_order')[:5]

    low_stock_products = products.filter(
        stock__lte=F('low_stock_threshold'),
    ).order_by('stock')[:10]

    return {
        'current_view': 'dashboard',
        'current_section': 'inventory',
        'total_products': total_products,
        'products_in_stock': products_in_stock,
        'products_low_stock': products_low_stock,
        'total_inventory_value': total_inventory_value,
        'currency': currency,
        'categories': categories,
        'low_stock_products': low_stock_products,
    }


# ---------------------------------------------------------------------------
# Products — List
# ---------------------------------------------------------------------------

@login_required
@with_module_nav('inventory', 'products')
@htmx_view('inventory/pages/products.html', 'inventory/partials/products_content.html')
def products_list(request):
    """Product list with search, sort, filter, pagination, export."""
    hub_id = request.session.get('hub_id')

    search_query = request.GET.get('q', '').strip()
    sort_field = request.GET.get('sort', 'name')
    sort_dir = request.GET.get('dir', 'asc')
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    page_number = request.GET.get('page', 1)
    current_view = request.GET.get('view', 'table')
    per_page = int(request.GET.get('per_page', 10))
    if per_page not in PER_PAGE_CHOICES:
        per_page = 10

    queryset = Product.objects.filter(
        hub_id=hub_id, is_deleted=False,
    ).prefetch_related('categories')

    # Status filter
    if status_filter == 'active':
        queryset = queryset.filter(is_active=True)
    elif status_filter == 'inactive':
        queryset = queryset.filter(is_active=False)
    elif status_filter == 'low_stock':
        queryset = queryset.filter(is_active=True, stock__lte=F('low_stock_threshold'), stock__gt=0)
    elif status_filter == 'out_of_stock':
        queryset = queryset.filter(is_active=True, stock=0)

    # Category filter
    if category_filter:
        queryset = queryset.filter(categories__id=category_filter)

    # Search
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(ean13__icontains=search_query) |
            Q(categories__name__icontains=search_query)
        ).distinct()

    # Sort
    order_by = PRODUCT_SORT_FIELDS.get(sort_field, 'name')
    if sort_dir == 'desc':
        order_by = f'-{order_by}'
    queryset = queryset.order_by(order_by)

    # Export (before pagination)
    export_format = request.GET.get('export')
    if export_format in ('csv', 'excel'):
        export_fields = ['name', 'sku', 'price', 'cost', 'stock', 'is_active']
        export_headers = [
            str(_('Name')), str(_('SKU')), str(_('Price')),
            str(_('Cost')), str(_('Stock')), str(_('Status')),
        ]
        export_formatters = {
            'is_active': lambda v: str(_('Active')) if v else str(_('Inactive')),
            'price': lambda v: str(v),
            'cost': lambda v: str(v),
        }
        if export_format == 'csv':
            return export_to_csv(
                queryset, fields=export_fields, headers=export_headers,
                field_formatters=export_formatters, filename='products.csv',
            )
        return export_to_excel(
            queryset, fields=export_fields, headers=export_headers,
            field_formatters=export_formatters, filename='products.xlsx',
            sheet_name=str(_('Products')),
        )

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page_number)

    categories_list = Category.objects.filter(
        hub_id=hub_id, is_deleted=False, is_active=True,
    ).order_by('sort_order', 'name')

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_field': sort_field,
        'sort_dir': sort_dir,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'categories_list': categories_list,
        'current_view': current_view,
        'per_page': per_page,
    }

    # HTMX partial: swap only datatable body
    if request.htmx and request.htmx.target == 'datatable-body':
        return django_render(request, 'inventory/partials/products_list.html', context)

    context.update({
        'current_section': 'inventory',
        'page_title': _('Products'),
    })
    return context


# ---------------------------------------------------------------------------
# Products — CRUD
# ---------------------------------------------------------------------------

@login_required
def product_add(request):
    """Add product — renders in side panel via HTMX."""
    hub_id = request.session.get('hub_id')
    categories_list = Category.objects.filter(
        hub_id=hub_id, is_deleted=False, is_active=True,
    ).order_by('sort_order', 'name')
    tax_classes = TaxClass.objects.filter(is_active=True).order_by('order', 'name')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        sku = request.POST.get('sku', '').strip()
        price_str = request.POST.get('price', '').strip()

        if not name or not sku or not price_str:
            return django_render(request, 'inventory/partials/panel_product_add.html', {
                'categories_list': categories_list,
                'tax_classes': tax_classes,
                'error': str(_('Name, SKU and Price are required')),
            })

        product = Product(
            hub_id=hub_id,
            name=name,
            sku=sku,
            description=request.POST.get('description', ''),
            product_type=request.POST.get('product_type', 'physical'),
            price=Decimal(price_str),
            cost=Decimal(request.POST.get('cost', '0') or '0'),
            stock=int(request.POST.get('stock', '0') or '0'),
            low_stock_threshold=int(request.POST.get('low_stock_threshold', '10') or '10'),
            ean13=request.POST.get('ean13', ''),
        )

        tax_class_id = request.POST.get('tax_class', '').strip()
        if tax_class_id:
            product.tax_class = TaxClass.objects.filter(id=tax_class_id, is_active=True).first()

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        product.save()

        cat_ids = request.POST.getlist('categories')
        if cat_ids:
            product.categories.set(cat_ids)

        return _render_products_list(request, hub_id)

    return django_render(request, 'inventory/partials/panel_product_add.html', {
        'categories_list': categories_list,
        'tax_classes': tax_classes,
    })


@login_required
def product_edit(request, pk):
    """Edit product — renders in side panel via HTMX."""
    hub_id = request.session.get('hub_id')
    product = get_object_or_404(Product, pk=pk, hub_id=hub_id, is_deleted=False)
    categories_list = Category.objects.filter(
        hub_id=hub_id, is_deleted=False, is_active=True,
    ).order_by('sort_order', 'name')
    tax_classes = TaxClass.objects.filter(is_active=True).order_by('order', 'name')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        sku = request.POST.get('sku', '').strip()
        price_str = request.POST.get('price', '').strip()

        if not name or not sku or not price_str:
            return django_render(request, 'inventory/partials/panel_product_edit.html', {
                'product': product,
                'categories_list': categories_list,
                'tax_classes': tax_classes,
                'error': str(_('Name, SKU and Price are required')),
            })

        product.name = name
        product.sku = sku
        product.description = request.POST.get('description', '')
        product.product_type = request.POST.get('product_type', 'physical')
        product.price = Decimal(price_str)
        product.cost = Decimal(request.POST.get('cost', '0') or '0')
        product.stock = int(request.POST.get('stock', '0') or '0')
        product.low_stock_threshold = int(request.POST.get('low_stock_threshold', '10') or '10')
        product.ean13 = request.POST.get('ean13', '')

        tax_class_id = request.POST.get('tax_class', '').strip()
        if tax_class_id:
            product.tax_class = TaxClass.objects.filter(id=tax_class_id, is_active=True).first()
        else:
            product.tax_class = None

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        product.save()

        cat_ids = request.POST.getlist('categories')
        product.categories.set(cat_ids)

        return _render_products_list(request, hub_id)

    return django_render(request, 'inventory/partials/panel_product_edit.html', {
        'product': product,
        'categories_list': categories_list,
        'tax_classes': tax_classes,
    })


@login_required
@require_POST
def product_delete(request, pk):
    """Soft-delete a product."""
    hub_id = request.session.get('hub_id')
    product = get_object_or_404(Product, pk=pk, hub_id=hub_id, is_deleted=False)

    product.is_deleted = True
    product.deleted_at = timezone.now()
    product.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    return _render_products_list(request, hub_id)


@login_required
@require_POST
def product_toggle_status(request, pk):
    """Toggle product active/inactive."""
    hub_id = request.session.get('hub_id')
    product = get_object_or_404(Product, pk=pk, hub_id=hub_id, is_deleted=False)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active', 'updated_at'])
    return _render_products_list(request, hub_id)


@login_required
@require_POST
def products_bulk_action(request):
    """Bulk activate/deactivate/delete products."""
    hub_id = request.session.get('hub_id')
    ids_str = request.POST.get('ids', '')
    action = request.POST.get('action', '')

    if not ids_str or not action:
        return _render_products_list(request, hub_id)

    ids = [uid.strip() for uid in ids_str.split(',') if uid.strip()]
    products = Product.objects.filter(hub_id=hub_id, is_deleted=False, id__in=ids)

    if action == 'activate':
        products.update(is_active=True)
    elif action == 'deactivate':
        products.update(is_active=False)
    elif action == 'delete':
        products.update(is_deleted=True, deleted_at=timezone.now())

    return _render_products_list(request, hub_id)


# ---------------------------------------------------------------------------
# Products — Import
# ---------------------------------------------------------------------------

@login_required
@require_POST
def products_import(request):
    """Import products from CSV or Excel file."""
    hub_id = request.session.get('hub_id')
    file = request.FILES.get('file')

    if not file:
        return _render_products_list(request, hub_id)

    try:
        rows = parse_import_file(file)
    except (ValueError, ImportError):
        return _render_products_list(request, hub_id)

    if not rows:
        return _render_products_list(request, hub_id)

    with transaction.atomic():
        for row_num, row in enumerate(rows, start=2):
            name = (row.get('Name') or row.get('name') or '').strip()
            sku = (row.get('SKU') or row.get('sku') or '').strip()
            price_str = (row.get('Price') or row.get('price') or '0').strip()
            cost_str = (row.get('Cost') or row.get('cost') or '0').strip()
            stock_str = (row.get('Stock') or row.get('stock') or '0').strip()

            if not name or not sku:
                continue

            try:
                price = Decimal(price_str)
                cost = Decimal(cost_str)
                stock = int(float(stock_str))
            except (ValueError, TypeError):
                continue

            existing = Product.objects.filter(hub_id=hub_id, sku=sku, is_deleted=False).first()
            if existing:
                existing.name = name
                existing.price = price
                existing.cost = cost
                existing.stock = stock
                existing.save()
                continue

            product = Product.objects.create(
                hub_id=hub_id,
                name=name,
                sku=sku,
                price=price,
                cost=cost,
                stock=stock,
                low_stock_threshold=int(float(
                    (row.get('Low Stock Threshold') or row.get('low_stock_threshold') or '10').strip() or '10'
                )),
                ean13=(row.get('EAN-13') or row.get('ean13') or '').strip(),
            )

            cats_str = (row.get('Categories') or row.get('categories') or '').strip()
            if cats_str:
                for cat_name in [c.strip() for c in cats_str.split(',') if c.strip()]:
                    normalized = cat_name.capitalize()
                    cat = Category.objects.filter(
                        hub_id=hub_id, is_deleted=False, name__iexact=normalized,
                    ).first()
                    if not cat:
                        cat = Category.objects.create(hub_id=hub_id, name=normalized)
                    product.categories.add(cat)

    return _render_products_list(request, hub_id)


# ---------------------------------------------------------------------------
# Categories — List
# ---------------------------------------------------------------------------

@login_required
@with_module_nav('inventory', 'categories')
@htmx_view('inventory/pages/categories.html', 'inventory/partials/categories_content.html')
def categories_index(request):
    """Category list with search, sort, filter, pagination, export."""
    hub_id = request.session.get('hub_id')

    search_query = request.GET.get('q', '').strip()
    sort_field = request.GET.get('sort', 'sort_order')
    sort_dir = request.GET.get('dir', 'asc')
    status_filter = request.GET.get('status', '')
    page_number = request.GET.get('page', 1)
    current_view = request.GET.get('view', 'table')
    per_page = int(request.GET.get('per_page', 10))
    if per_page not in PER_PAGE_CHOICES:
        per_page = 10

    queryset = Category.objects.filter(hub_id=hub_id, is_deleted=False)

    # Status filter
    if status_filter == 'active':
        queryset = queryset.filter(is_active=True)
    elif status_filter == 'inactive':
        queryset = queryset.filter(is_active=False)

    # Search
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Sort
    order_by = CATEGORY_SORT_FIELDS.get(sort_field, 'sort_order')
    if sort_dir == 'desc':
        order_by = f'-{order_by}'
    queryset = queryset.order_by(order_by, 'name')

    # Export (before pagination)
    export_format = request.GET.get('export')
    if export_format in ('csv', 'excel'):
        export_fields = ['name', 'description', 'icon', 'color', 'sort_order', 'is_active']
        export_headers = [
            str(_('Name')), str(_('Description')), str(_('Icon')),
            str(_('Color')), str(_('Order')), str(_('Status')),
        ]
        export_formatters = {
            'is_active': lambda v: str(_('Active')) if v else str(_('Inactive')),
        }
        if export_format == 'csv':
            return export_to_csv(
                queryset, fields=export_fields, headers=export_headers,
                field_formatters=export_formatters, filename='categories.csv',
            )
        return export_to_excel(
            queryset, fields=export_fields, headers=export_headers,
            field_formatters=export_formatters, filename='categories.xlsx',
            sheet_name=str(_('Categories')),
        )

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page_number)

    context = {
        'categories': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'sort_field': sort_field,
        'sort_dir': sort_dir,
        'status_filter': status_filter,
        'current_view': current_view,
        'per_page': per_page,
    }

    # HTMX partial: swap only datatable body
    if request.htmx and request.htmx.target == 'datatable-body':
        return django_render(request, 'inventory/partials/categories_list.html', context)

    context.update({
        'current_section': 'inventory',
        'page_title': _('Categories'),
    })
    return context


# ---------------------------------------------------------------------------
# Categories — CRUD
# ---------------------------------------------------------------------------

@login_required
def category_add(request):
    """Add category — renders in side panel via HTMX."""
    hub_id = request.session.get('hub_id')
    tax_classes = TaxClass.objects.filter(is_active=True).order_by('order', 'name')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            return django_render(request, 'inventory/partials/panel_category_add.html', {
                'tax_classes': tax_classes,
                'error': str(_('Name is required')),
            })

        tax_class = None
        tax_class_id = request.POST.get('tax_class', '').strip()
        if tax_class_id:
            tax_class = TaxClass.objects.filter(id=tax_class_id, is_active=True).first()

        category = Category(
            hub_id=hub_id,
            name=name,
            description=request.POST.get('description', ''),
            icon=request.POST.get('icon', 'cube-outline'),
            color=request.POST.get('color', '#3880ff'),
            sort_order=int(request.POST.get('sort_order', '0') or '0'),
            tax_class=tax_class,
        )

        if 'image' in request.FILES:
            category.image = request.FILES['image']

        category.save()
        return _render_categories_list(request, hub_id)

    return django_render(request, 'inventory/partials/panel_category_add.html', {
        'tax_classes': tax_classes,
    })


@login_required
def category_edit(request, pk):
    """Edit category — renders in side panel via HTMX."""
    hub_id = request.session.get('hub_id')
    category = get_object_or_404(Category, pk=pk, hub_id=hub_id, is_deleted=False)
    tax_classes = TaxClass.objects.filter(is_active=True).order_by('order', 'name')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()

        if not name:
            return django_render(request, 'inventory/partials/panel_category_edit.html', {
                'category': category,
                'tax_classes': tax_classes,
                'error': str(_('Name is required')),
            })

        category.name = name
        category.description = request.POST.get('description', '')
        category.icon = request.POST.get('icon', 'cube-outline')
        category.color = request.POST.get('color', '#3880ff')
        category.sort_order = int(request.POST.get('sort_order', '0') or '0')

        tax_class_id = request.POST.get('tax_class', '').strip()
        if tax_class_id:
            category.tax_class = TaxClass.objects.filter(id=tax_class_id, is_active=True).first()
        else:
            category.tax_class = None

        if 'image' in request.FILES:
            category.image = request.FILES['image']

        category.save()
        return _render_categories_list(request, hub_id)

    return django_render(request, 'inventory/partials/panel_category_edit.html', {
        'category': category,
        'tax_classes': tax_classes,
    })


@login_required
@require_POST
def category_delete(request, pk):
    """Soft-delete a category."""
    hub_id = request.session.get('hub_id')
    category = get_object_or_404(Category, pk=pk, hub_id=hub_id, is_deleted=False)

    category.is_deleted = True
    category.deleted_at = timezone.now()
    category.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    return _render_categories_list(request, hub_id)


@login_required
@require_POST
def category_toggle_status(request, pk):
    """Toggle category active/inactive."""
    hub_id = request.session.get('hub_id')
    category = get_object_or_404(Category, pk=pk, hub_id=hub_id, is_deleted=False)
    category.is_active = not category.is_active
    category.save(update_fields=['is_active', 'updated_at'])
    return _render_categories_list(request, hub_id)


@login_required
@require_POST
def categories_bulk_action(request):
    """Bulk activate/deactivate/delete categories."""
    hub_id = request.session.get('hub_id')
    ids_str = request.POST.get('ids', '')
    action = request.POST.get('action', '')

    if not ids_str or not action:
        return _render_categories_list(request, hub_id)

    ids = [uid.strip() for uid in ids_str.split(',') if uid.strip()]
    categories = Category.objects.filter(hub_id=hub_id, is_deleted=False, id__in=ids)

    if action == 'activate':
        categories.update(is_active=True)
    elif action == 'deactivate':
        categories.update(is_active=False)
    elif action == 'delete':
        categories.update(is_deleted=True, deleted_at=timezone.now())

    return _render_categories_list(request, hub_id)


# ---------------------------------------------------------------------------
# Categories — Import
# ---------------------------------------------------------------------------

@login_required
@require_POST
def categories_import(request):
    """Import categories from CSV or Excel file."""
    hub_id = request.session.get('hub_id')
    file = request.FILES.get('file')

    if not file:
        return _render_categories_list(request, hub_id)

    try:
        rows = parse_import_file(file)
    except (ValueError, ImportError):
        return _render_categories_list(request, hub_id)

    if not rows:
        return _render_categories_list(request, hub_id)

    with transaction.atomic():
        for row_num, row in enumerate(rows, start=2):
            name = (row.get('Name') or row.get('name') or '').strip()

            if not name:
                continue

            normalized = name.capitalize()
            existing = Category.objects.filter(
                hub_id=hub_id, is_deleted=False, name__iexact=normalized,
            ).first()

            if existing:
                continue

            Category.objects.create(
                hub_id=hub_id,
                name=normalized,
                description=(row.get('Description') or row.get('description') or '').strip(),
                icon=(row.get('Icon') or row.get('icon') or 'cube-outline').strip(),
                color=(row.get('Color') or row.get('color') or '#3880ff').strip(),
                sort_order=int(float(
                    (row.get('Order') or row.get('order') or row.get('Sort Order') or '0').strip() or '0'
                )),
            )

    return _render_categories_list(request, hub_id)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@login_required
@with_module_nav('inventory', 'reports')
@htmx_view('inventory/pages/reports.html', 'inventory/partials/reports_content.html')
def reports_view(request):
    """Inventory reports and analytics."""
    hub_id = request.session.get('hub_id')

    products = Product.objects.filter(hub_id=hub_id, is_deleted=False, is_active=True)

    total_products = products.count()
    products_in_stock = products.filter(stock__gt=0).count()
    products_out_of_stock = products.filter(stock=0).count()
    products_low_stock = products.filter(
        stock__lte=F('low_stock_threshold'), stock__gt=0,
    ).count()

    total_inventory_value = products.aggregate(
        total=Sum(F('stock') * F('price'))
    )['total'] or 0
    total_cost_value = products.aggregate(
        total=Sum(F('stock') * F('cost'))
    )['total'] or 0
    total_units = products.aggregate(total=Sum('stock'))['total'] or 0
    total_categories = Category.objects.filter(
        hub_id=hub_id, is_deleted=False, is_active=True,
    ).count()

    category_stats = []
    categories = Category.objects.filter(
        hub_id=hub_id, is_deleted=False, is_active=True,
    ).order_by('sort_order', 'name')
    for cat in categories:
        cat_products = products.filter(categories=cat)
        count = cat_products.count()
        if count > 0:
            category_stats.append({
                'name': cat.name,
                'icon': cat.icon,
                'color': cat.color,
                'product_count': count,
                'total_stock': cat_products.aggregate(total=Sum('stock'))['total'] or 0,
                'total_value': cat_products.aggregate(
                    total=Sum(F('stock') * F('price'))
                )['total'] or 0,
            })

    top_products_by_value = products.filter(stock__gt=0).annotate(
        stock_value=F('stock') * F('price'),
    ).order_by('-stock_value')[:10]

    top_products_by_stock = products.filter(stock__gt=0).order_by('-stock')[:10]

    critical_stock_products = products.filter(
        stock__lte=F('low_stock_threshold'), stock__gt=0,
    ).order_by('stock')[:20]

    return {
        'current_view': 'reports',
        'current_section': 'inventory',
        'total_products': total_products,
        'products_in_stock': products_in_stock,
        'products_out_of_stock': products_out_of_stock,
        'products_low_stock': products_low_stock,
        'total_inventory_value': total_inventory_value,
        'total_cost_value': total_cost_value,
        'total_units': total_units,
        'total_categories': total_categories,
        'category_stats': category_stats,
        'top_products_by_value': top_products_by_value,
        'top_products_by_stock': top_products_by_stock,
        'critical_stock_products': critical_stock_products,
    }


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@login_required
@with_module_nav('inventory', 'settings')
@htmx_view('inventory/pages/settings.html', 'inventory/partials/settings_content.html')
def settings_view(request):
    """Inventory settings."""
    hub_id = request.session.get('hub_id')
    settings = InventorySettings.get_settings(hub_id)

    if request.method == 'POST':
        settings.allow_negative_stock = request.POST.get('allow_negative_stock') == 'on'
        settings.low_stock_alert_enabled = request.POST.get('low_stock_alert_enabled') == 'on'
        settings.auto_generate_sku = request.POST.get('auto_generate_sku') == 'on'
        settings.barcode_enabled = request.POST.get('barcode_enabled') == 'on'
        settings.save()

        import json
        response = HttpResponse(status=200)
        response['HX-Trigger'] = json.dumps({
            'showMessage': {'message': str(_('Settings saved successfully')), 'type': 'success'}
        })
        return response

    return {
        'current_view': 'settings',
        'current_section': 'inventory',
        'config': settings,
    }


# ---------------------------------------------------------------------------
# Barcode
# ---------------------------------------------------------------------------

@login_required
def generate_barcode(request, product_id):
    """Generate barcode SVG for a product."""
    from .barcode_utils import generate_barcode_svg

    hub_id = request.session.get('hub_id')
    settings = InventorySettings.get_settings(hub_id)

    if not settings.barcode_enabled:
        return HttpResponse('<svg></svg>', content_type='image/svg+xml', status=403)

    try:
        product = get_object_or_404(
            Product, id=product_id, hub_id=hub_id, is_deleted=False,
        )
        barcode_type = request.GET.get('type', 'sku')

        if barcode_type == 'ean13':
            if not product.ean13:
                return HttpResponse(
                    '<svg><text x="50%" y="50%" text-anchor="middle" fill="red">'
                    'No EAN-13</text></svg>',
                    content_type='image/svg+xml',
                )
            svg_content = generate_barcode_svg(product.ean13, format_type='ean13')
        else:
            svg_content = generate_barcode_svg(product.sku, format_type='code128')

        return HttpResponse(svg_content, content_type='image/svg+xml')

    except ValueError:
        return HttpResponse('<svg></svg>', content_type='image/svg+xml', status=400)
    except Exception:
        return HttpResponse('<svg></svg>', content_type='image/svg+xml', status=500)
