from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),  # Main inventory dashboard

    # Products
    path('products/', views.products_list, name='products_list'),  # Products list with DataTable
    path('products/api/list/', views.product_list_ajax, name='product_list_ajax'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_view, name='product_view'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('products/<int:product_id>/barcode/', views.generate_barcode, name='generate_barcode'),
    path('products/export/csv/', views.export_csv, name='export_csv'),
    path('products/export/excel/', views.export_csv, name='export_excel'),  # Mismo handler, detecta por query param
    path('products/import/csv/', views.import_csv, name='import_csv'),
    path('products/import/excel/', views.import_excel, name='import_excel'),

    # Categories
    path('categories/', views.categories_index, name='categories_index'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/edit/<int:pk>/', views.category_edit, name='category_edit'),
    path('categories/delete/<int:pk>/', views.category_delete, name='category_delete'),
    path('categories/api/', views.categories_list, name='categories_list'),

    # Reports
    path('reports/', views.reports_view, name='reports'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
]
