from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Category, Product, ProductVariant, Warehouse, InventorySettings


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            'name', 'description', 'icon', 'color', 'image',
            'tax_class', 'is_active', 'sort_order',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Category name'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': 2,
                'placeholder': _('Description'),
            }),
            'icon': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'cube-outline',
            }),
            'color': forms.TextInput(attrs={
                'class': 'input',
                'type': 'color',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'input',
            }),
            'tax_class': forms.Select(attrs={
                'class': 'select',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'input',
                'min': '0',
            }),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'ean13', 'description', 'product_type',
            'price', 'cost', 'stock', 'low_stock_threshold',
            'categories', 'tax_class', 'image', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Product name'),
            }),
            'sku': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('SKU'),
            }),
            'ean13': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('EAN-13 (optional)'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': 3,
                'placeholder': _('Product description'),
            }),
            'product_type': forms.Select(attrs={
                'class': 'select',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'input',
                'step': '0.01',
                'min': '0',
            }),
            'cost': forms.NumberInput(attrs={
                'class': 'input',
                'step': '0.01',
                'min': '0',
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'input',
                'min': '0',
            }),
            'low_stock_threshold': forms.NumberInput(attrs={
                'class': 'input',
                'min': '0',
            }),
            'categories': forms.SelectMultiple(attrs={
                'class': 'select',
            }),
            'tax_class': forms.Select(attrs={
                'class': 'select',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'input',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['name', 'sku', 'price', 'stock', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Variant name (e.g. Red XL)'),
            }),
            'sku': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Variant SKU'),
            }),
            'price': forms.NumberInput(attrs={
                'class': 'input',
                'step': '0.01',
                'min': '0',
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'input',
                'min': '0',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'input',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
        }


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'code', 'address', 'is_active', 'is_default', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Warehouse name'),
            }),
            'code': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('WH-01'),
            }),
            'address': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': 2,
                'placeholder': _('Address'),
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'input',
                'min': '0',
            }),
        }


class InventorySettingsForm(forms.ModelForm):
    class Meta:
        model = InventorySettings
        fields = [
            'allow_negative_stock', 'low_stock_alert_enabled',
            'auto_generate_sku', 'barcode_enabled',
        ]
        widgets = {
            'allow_negative_stock': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'low_stock_alert_enabled': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'auto_generate_sku': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'barcode_enabled': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
        }
