from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Products
    path('products/', views.index, name='products_index'),
    path('products/api/list/', views.product_list_ajax, name='product_list_ajax'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('products/delete/<int:pk>/', views.product_delete, name='product_delete'),
    path('products/export/csv/', views.export_csv, name='export_csv'),
    path('products/import/csv/', views.import_csv, name='import_csv'),
    path('products/import/excel/', views.import_excel, name='import_excel'),

    # Categories
    path('categories/', views.categories_index, name='categories_index'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/edit/<int:pk>/', views.category_edit, name='category_edit'),
    path('categories/delete/<int:pk>/', views.category_delete, name='category_delete'),
    path('categories/api/', views.categories_list, name='categories_list'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
]
