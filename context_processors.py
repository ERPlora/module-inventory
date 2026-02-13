"""
Context processors for Inventory module.

Makes module-specific configuration available in all inventory templates.
Note: hub_config and store_config are already available globally via
apps.core.context_processors.hub_config_context
"""


def inventory_settings(request):
    """
    Add inventory settings to template context.
    """
    from .models import InventorySettings

    try:
        hub_id = request.session.get('hub_id')
        if hub_id:
            settings_obj = InventorySettings.get_settings(hub_id)
        else:
            settings_obj = None
    except Exception:
        settings_obj = None

    return {
        'inventory_settings': settings_obj,
    }
