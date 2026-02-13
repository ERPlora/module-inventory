from django.utils.translation import gettext_lazy as _

MODULE_ID = 'inventory'
MODULE_NAME = _('Inventory')
MODULE_ICON = 'cube-outline'

MENU = {
    'label': _('Inventory'),
    'icon': 'cube-outline',
    'order': 10,
}

NAVIGATION = [
    {'label': _('Dashboard'), 'icon': 'speedometer-outline', 'id': 'dashboard'},
    {'label': _('Products'), 'icon': 'storefront-outline', 'id': 'products'},
    {'label': _('Categories'), 'icon': 'pricetags-outline', 'id': 'categories'},
    {'label': _('Reports'), 'icon': 'bar-chart-outline', 'id': 'reports'},
    {'label': _('Settings'), 'icon': 'settings-outline', 'id': 'settings'},
]

PERMISSIONS = [
    'inventory.view_product',
    'inventory.add_product',
    'inventory.change_product',
    'inventory.delete_product',
    'inventory.view_category',
    'inventory.add_category',
    'inventory.change_category',
    'inventory.delete_category',
    'inventory.view_warehouse',
    'inventory.add_warehouse',
    'inventory.change_warehouse',
    'inventory.view_stockmovement',
    'inventory.add_stockmovement',
    'inventory.view_reports',
    'inventory.manage_settings',
]
