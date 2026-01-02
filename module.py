"""
Inventory Module Configuration

This file defines the module metadata and navigation for the Inventory module.
Used by the @module_view decorator to automatically render navigation tabs.
"""
from django.utils.translation import gettext_lazy as _

# Module Identification
MODULE_ID = "inventory"
MODULE_NAME = _("Inventory")
MODULE_ICON = "cube-outline"
MODULE_VERSION = "1.0.0"
MODULE_CATEGORY = "inventory"

# Target Industries (business verticals this module is designed for)
MODULE_INDUSTRIES = [
    "retail",        # Retail stores
    "wholesale",     # Wholesale distributors
    "restaurant",    # Restaurants
    "bar",           # Bars & pubs
    "cafe",          # Cafes & bakeries
    "fast_food",     # Fast food
    "salon",         # Beauty & wellness
    "manufacturing", # Manufacturing
]

# Sidebar Menu Configuration
# This controls how the module appears in the main sidebar
MENU = {
    "label": _("Inventory"),
    "icon": "cube-outline",
    "order": 10,
    "show": True,
}

# Internal Navigation (Tabs)
# These are the tabs shown at the bottom when inside the module
# - id: unique identifier for the tab (matches view_id in @module_view)
# - label: displayed text (use gettext for i18n)
# - icon: Ionicons icon name
# - view: the view name from urls.py (URL will be /m/inventory/{view}/)
NAVIGATION = [
    {
        "id": "dashboard",
        "label": _("Overview"),
        "icon": "grid-outline",
        "view": "",  # Empty string for index/root
    },
    {
        "id": "products",
        "label": _("Products"),
        "icon": "cube-outline",
        "view": "products",
    },
    {
        "id": "categories",
        "label": _("Categories"),
        "icon": "albums-outline",
        "view": "categories",
    },
    {
        "id": "reports",
        "label": _("Reports"),
        "icon": "stats-chart-outline",
        "view": "reports",
    },
    {
        "id": "settings",
        "label": _("Settings"),
        "icon": "settings-outline",
        "view": "settings",
    },
]

# Module Dependencies
DEPENDENCIES = []

# Default Settings
SETTINGS = {
    "allow_negative_stock": False,
    "low_stock_alert_enabled": True,
    "items_per_page": 20,
}

# Permissions
PERMISSIONS = [
    "inventory.view_product",
    "inventory.add_product",
    "inventory.change_product",
    "inventory.delete_product",
    "inventory.view_category",
    "inventory.add_category",
    "inventory.change_category",
    "inventory.delete_category",
]
