"""
Context processors for Inventory plugin.

Makes plugin-specific configuration available in all inventory templates.
Note: hub_config and store_config are already available globally via
apps.core.context_processors.hub_config_context
"""


def inventory_settings(request):
    """
    Add inventory plugin settings to template context.

    This makes the following available in all inventory templates:
    - inventory_settings: Plugin-specific configuration (low stock threshold, etc.)
    """
    from .models import InventorySettings

    try:
        settings_obj = InventorySettings.get_settings()
    except Exception:
        settings_obj = None

    return {
        'inventory_settings': settings_obj
    }
