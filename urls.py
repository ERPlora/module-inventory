from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Products
    path('products/', views.products_list, name='products_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<uuid:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<uuid:pk>/delete/', views.product_delete, name='product_delete'),
    path('products/<uuid:pk>/toggle/', views.product_toggle_status, name='product_toggle_status'),
    path('products/bulk/', views.products_bulk_action, name='products_bulk_action'),
    path('products/import/', views.products_import, name='products_import'),
    path('products/<uuid:product_id>/barcode/', views.generate_barcode, name='generate_barcode'),

    # Categories
    path('categories/', views.categories_index, name='categories_index'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<uuid:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<uuid:pk>/delete/', views.category_delete, name='category_delete'),
    path('categories/<uuid:pk>/toggle/', views.category_toggle_status, name='category_toggle_status'),
    path('categories/bulk/', views.categories_bulk_action, name='categories_bulk_action'),
    path('categories/import/', views.categories_import, name='categories_import'),

    # Reports
    path('reports/', views.reports_view, name='reports'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
]
