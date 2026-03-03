from django.utils.translation import gettext_lazy as _

MODULE_ID = 'inventory'
MODULE_NAME = _('Inventory')
MODULE_VERSION = '1.0.0'
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

ROLE_PERMISSIONS = {
    "admin": ["*"],
    "manager": [
        "add_category",
        "add_product",
        "add_stockmovement",
        "add_warehouse",
        "change_category",
        "change_product",
        "change_warehouse",
        "view_category",
        "view_product",
        "view_reports",
        "view_stockmovement",
        "view_warehouse",
    ],
    "employee": [
        "add_product",
        "view_category",
        "view_product",
        "view_stockmovement",
        "view_warehouse",
    ],
}
