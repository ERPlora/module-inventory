from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/list/', views.product_list_ajax, name='product_list_ajax'),
    path('api/categories/', views.categories_list, name='categories_list'),
    path('create/', views.product_create, name='product_create'),
    path('edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('delete/<int:pk>/', views.product_delete, name='product_delete'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('import/csv/', views.import_csv, name='import_csv'),
    path('import/excel/', views.import_excel, name='import_excel'),
]
