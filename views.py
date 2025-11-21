import csv
import io
import os
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from apps.accounts.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, F
from django.db import models, transaction
from django.conf import settings
from .models import Product, Category


@login_required
def index(request):
    """
    Vista principal del plugin de productos
    """
    # Estadísticas
    total_products = Product.objects.filter(is_active=True).count()
    products_in_stock = Product.objects.filter(is_active=True, stock__gt=0).count()
    products_low_stock = Product.objects.filter(is_active=True).filter(
        stock__lte=F('low_stock_threshold')
    ).count()
    total_inventory_value = Product.objects.filter(is_active=True).aggregate(
        total=Sum(F('stock') * F('price'))
    )['total'] or 0

    context = {
        'current_view': 'products',
        'total_products': total_products,
        'products_in_stock': products_in_stock,
        'products_low_stock': products_low_stock,
        'total_inventory_value': total_inventory_value,
    }
    return render(request, 'inventory/index.html', context)


@login_required
def product_list_ajax(request):
    """
    Retorna la lista de productos en formato JSON para tabla dinámica
    """
    search = request.GET.get('search', '')
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 10))

    # Filtros
    products_queryset = Product.objects.filter(is_active=True)

    if search:
        products_queryset = products_queryset.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search) |
            Q(category__name__icontains=search)
        )

    # Paginación
    paginator = Paginator(products_queryset, per_page)
    page_obj = paginator.get_page(page)

    products_data = []
    for product in page_obj:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'category': product.category.name if product.category else 'General',
            'category_id': product.category.id if product.category else None,
            'price': float(product.price),
            'cost': float(product.cost),
            'stock': product.stock,
            'low_stock_threshold': product.low_stock_threshold,
            'is_low_stock': product.is_low_stock,
            'image': product.get_image_path(),
            'initial': product.get_initial(),
            'profit_margin': float(product.profit_margin),
        })

    return JsonResponse({
        'products': products_data,
        'total': paginator.count,
        'pages': paginator.num_pages,
        'current_page': page_obj.number,
    })


@login_required
@require_http_methods(["GET", "POST"])
def product_create(request):
    """
    Crear un nuevo producto
    """
    if request.method == 'POST':
        try:
            # Procesar imagen
            image = request.FILES.get('image')

            # Get or create category
            category_id = request.POST.get('category_id')
            category = None
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    category = Category.objects.get(name='General')
            else:
                category = Category.objects.get(name='General')

            product = Product.objects.create(
                name=request.POST['name'],
                sku=request.POST['sku'],
                description=request.POST.get('description', ''),
                price=Decimal(request.POST['price']),
                cost=Decimal(request.POST.get('cost', '0')),
                stock=int(request.POST.get('stock', 0)),
                low_stock_threshold=int(request.POST.get('low_stock_threshold', 10)),
                category=category,
                image=image
            )

            return JsonResponse({
                'success': True,
                'message': 'Producto creado exitosamente',
                'product_id': product.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

    return render(request, 'inventory/create.html')


@login_required
@require_http_methods(["GET", "POST"])
def product_edit(request, pk):
    """
    Editar un producto existente
    """
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        try:
            product.name = request.POST['name']
            product.sku = request.POST['sku']
            product.description = request.POST.get('description', '')
            product.price = Decimal(request.POST['price'])
            product.cost = Decimal(request.POST.get('cost', '0'))
            product.stock = int(request.POST.get('stock', 0))
            product.low_stock_threshold = int(request.POST.get('low_stock_threshold', 10))

            # Update category
            category_id = request.POST.get('category_id')
            if category_id:
                try:
                    product.category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    product.category = Category.objects.get(name='General')
            else:
                product.category = Category.objects.get(name='General')

            # Actualizar imagen si se proporciona
            if 'image' in request.FILES:
                # Eliminar imagen anterior
                if product.image:
                    if os.path.isfile(product.image.path):
                        os.remove(product.image.path)
                product.image = request.FILES['image']

            product.save()

            return JsonResponse({
                'success': True,
                'message': 'Producto actualizado exitosamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

    context = {'product': product}
    return render(request, 'inventory/edit.html', context)


@login_required
@require_http_methods(["POST"])
def product_delete(request, pk):
    """
    Eliminar un producto
    """
    try:
        product = get_object_or_404(Product, pk=pk)
        product.delete()

        return JsonResponse({
            'success': True,
            'message': 'Producto eliminado exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
def export_csv(request):
    """
    Exportar productos a CSV
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="productos.csv"'
    response.write('\ufeff')  # BOM para UTF-8

    writer = csv.writer(response)
    writer.writerow(['SKU', 'Nombre', 'Descripción', 'Categoría', 'Precio', 'Costo', 'Stock', 'Umbral Stock Bajo'])

    products = Product.objects.filter(is_active=True)
    for product in products:
        writer.writerow([
            product.sku,
            product.name,
            product.description,
            product.category.name if product.category else 'General',
            float(product.price),
            float(product.cost),
            product.stock,
            product.low_stock_threshold,
        ])

    return response


@login_required
@require_http_methods(["POST"])
def import_csv(request):
    """
    Importar productos desde CSV
    """
    try:
        csv_file = request.FILES.get('file')

        if not csv_file:
            return JsonResponse({
                'success': False,
                'message': 'No se proporcionó ningún archivo'
            }, status=400)

        if not csv_file.name.endswith('.csv'):
            return JsonResponse({
                'success': False,
                'message': 'El archivo debe ser CSV'
            }, status=400)

        # Leer CSV
        decoded_file = csv_file.read().decode('utf-8-sig')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        created = 0
        updated = 0
        errors = []

        with transaction.atomic():
            for row in reader:
                try:
                    sku = row.get('SKU', '').strip()
                    if not sku:
                        continue

                    # Validations
                    name = row.get('Nombre', '').strip()
                    if not name:
                        errors.append(f"Fila {reader.line_num}: El nombre es obligatorio")
                        continue

                    price = Decimal(row.get('Precio', '0'))
                    cost = Decimal(row.get('Costo', '0'))
                    stock = int(row.get('Stock', '0'))

                    if price < 0:
                        errors.append(f"Fila {reader.line_num}: El precio no puede ser negativo")
                        continue

                    if cost < 0:
                        errors.append(f"Fila {reader.line_num}: El costo no puede ser negativo")
                        continue

                    if stock < 0:
                        errors.append(f"Fila {reader.line_num}: El stock no puede ser negativo")
                        continue

                    # Get or create category
                    category_name = row.get('Categoría', 'General').strip()
                    category, _ = Category.objects.get_or_create(
                        name=category_name,
                        defaults={'icon': 'cube-outline', 'is_active': True}
                    )

                    product, is_created = Product.objects.update_or_create(
                        sku=sku,
                        defaults={
                            'name': name,
                            'description': row.get('Descripción', ''),
                            'category': category,
                            'price': price,
                            'cost': cost,
                            'stock': stock,
                            'low_stock_threshold': int(row.get('Umbral Stock Bajo', '10')),
                        }
                    )

                    if is_created:
                        created += 1
                    else:
                        updated += 1

                except Exception as e:
                    errors.append(f"Error en fila {reader.line_num}: {str(e)}")

        return JsonResponse({
            'success': True,
            'message': f'{created} productos creados, {updated} actualizados',
            'created': created,
            'updated': updated,
            'errors': errors
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al importar: {str(e)}'
        }, status=400)


@login_required
@require_http_methods(["POST"])
def import_excel(request):
    """
    Importar productos desde Excel
    Requiere openpyxl: pip install openpyxl
    """
    try:
        excel_file = request.FILES.get('file')

        if not excel_file:
            return JsonResponse({
                'success': False,
                'message': 'No se proporcionó ningún archivo'
            }, status=400)

        if not (excel_file.name.endswith('.xlsx') or excel_file.name.endswith('.xls')):
            return JsonResponse({
                'success': False,
                'message': 'El archivo debe ser Excel (.xlsx o .xls)'
            }, status=400)

        try:
            import openpyxl
        except ImportError:
            return JsonResponse({
                'success': False,
                'message': 'Librería openpyxl no instalada. Ejecute: pip install openpyxl'
            }, status=400)

        # Leer Excel
        wb = openpyxl.load_workbook(excel_file)
        ws = wb.active

        # Obtener encabezados (primera fila)
        headers = [cell.value for cell in ws[1]]

        created = 0
        updated = 0
        errors = []

        with transaction.atomic():
            for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                try:
                    row_dict = dict(zip(headers, row))

                    sku = str(row_dict.get('SKU', '')).strip()
                    if not sku:
                        continue

                    # Validations
                    name = str(row_dict.get('Nombre', '')).strip()
                    if not name:
                        errors.append(f"Fila {row_idx}: El nombre es obligatorio")
                        continue

                    price = Decimal(str(row_dict.get('Precio', '0')))
                    cost = Decimal(str(row_dict.get('Costo', '0')))
                    stock = int(row_dict.get('Stock', 0))

                    if price < 0:
                        errors.append(f"Fila {row_idx}: El precio no puede ser negativo")
                        continue

                    if cost < 0:
                        errors.append(f"Fila {row_idx}: El costo no puede ser negativo")
                        continue

                    if stock < 0:
                        errors.append(f"Fila {row_idx}: El stock no puede ser negativo")
                        continue

                    # Get or create category
                    category_name = str(row_dict.get('Categoría', 'General')).strip()
                    category, _ = Category.objects.get_or_create(
                        name=category_name,
                        defaults={'icon': 'cube-outline', 'is_active': True}
                    )

                    product, is_created = Product.objects.update_or_create(
                        sku=sku,
                        defaults={
                            'name': name,
                            'description': str(row_dict.get('Descripción', '')),
                            'category': category,
                            'price': price,
                            'cost': cost,
                            'stock': stock,
                            'low_stock_threshold': int(row_dict.get('Umbral Stock Bajo', 10)),
                        }
                    )

                    if is_created:
                        created += 1
                    else:
                        updated += 1

                except Exception as e:
                    errors.append(f"Error en fila {row_idx}: {str(e)}")

        return JsonResponse({
            'success': True,
            'message': f'{created} productos creados, {updated} actualizados',
            'created': created,
            'updated': updated,
            'errors': errors
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al importar: {str(e)}'
        }, status=400)


@login_required
def categories_list(request):
    """
    Retorna la lista de categorías para dropdowns
    """
    categories = Category.objects.filter(is_active=True).order_by('order', 'name')
    categories_data = [
        {
            'id': category.id,
            'name': category.name,
            'icon': category.icon,
            'color': category.color,
            'image': category.get_image_url(),
            'initial': category.get_initial(),
            'product_count': category.product_count,
        }
        for category in categories
    ]

    return JsonResponse({
        'categories': categories_data
    })


@login_required
def categories_index(request):
    """Vista principal de gestión de categorías."""
    categories = Category.objects.filter(is_active=True).order_by('order', 'name')

    context = {
        'categories': categories,
        'total_categories': categories.count()
    }
    return render(request, 'inventory/categories.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def category_create(request):
    """Crear una nueva categoría."""
    if request.method == 'POST':
        try:
            image = request.FILES.get('image')

            category = Category.objects.create(
                name=request.POST['name'],
                description=request.POST.get('description', ''),
                icon=request.POST.get('icon', 'cube-outline'),
                color=request.POST.get('color', '#3880ff'),
                order=int(request.POST.get('order', 0)),
                image=image
            )

            return JsonResponse({
                'success': True,
                'message': 'Categoría creada exitosamente',
                'category_id': category.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

    return render(request, 'inventory/category_create.html')


@login_required
@require_http_methods(["GET", "POST"])
def category_edit(request, pk):
    """Editar una categoría existente."""
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        try:
            category.name = request.POST['name']
            category.description = request.POST.get('description', '')
            category.icon = request.POST.get('icon', 'cube-outline')
            category.color = request.POST.get('color', '#3880ff')
            category.order = int(request.POST.get('order', 0))

            # Actualizar imagen si se proporciona
            if 'image' in request.FILES:
                if category.image:
                    if os.path.isfile(category.image.path):
                        os.remove(category.image.path)
                category.image = request.FILES['image']

            category.save()

            return JsonResponse({
                'success': True,
                'message': 'Categoría actualizada exitosamente'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

    context = {'category': category}
    return render(request, 'inventory/category_edit.html', context)


@login_required
@require_http_methods(["POST"])
def category_delete(request, pk):
    """Eliminar una categoría."""
    try:
        category = get_object_or_404(Category, pk=pk)

        # Check if category has products
        product_count = category.products.filter(is_active=True).count()
        if product_count > 0:
            return JsonResponse({
                'success': False,
                'message': f'No se puede eliminar la categoría porque tiene {product_count} productos asociados'
            }, status=400)

        category.delete()

        return JsonResponse({
            'success': True,
            'message': 'Categoría eliminada exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required
def settings_view(request):
    """Vista de configuración del plugin de productos"""
    import json
    from .models import ProductsConfig

    config = ProductsConfig.get_config()

    if request.method == "POST":
        try:
            # Parse JSON body
            data = json.loads(request.body)

            # Update config
            config.allow_negative_stock = data.get('allow_negative_stock', False)
            config.low_stock_alert_enabled = data.get('low_stock_alert_enabled', True)
            config.save()

            return JsonResponse({"success": True, "message": "Configuración guardada correctamente"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)

    context = {
        "config": config,
    }
    return render(request, "inventory/settings.html", context)

