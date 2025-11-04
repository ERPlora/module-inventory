from django.contrib import admin
from .models import Product, Category


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'price', 'cost', 'stock', 'is_low_stock', 'is_active']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'sku', 'description']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'sku', 'description', 'category', 'is_active')
        }),
        ('Precios y Stock', {
            'fields': ('price', 'cost', 'stock', 'low_stock_threshold')
        }),
        ('Imagen', {
            'fields': ('image',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'color', 'order', 'product_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'slug', 'description']
    list_editable = ['is_active', 'order']
    readonly_fields = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
