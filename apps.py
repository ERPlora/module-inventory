from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'
    verbose_name = 'Gestión de Inventario'

    def ready(self):
        """
        Register extension points for the Inventory module.

        This module EMITS signals:
        - product_created: When a new product is created
        - product_updated: When a product is modified
        - product_deleted: When a product is deleted
        - stock_changed: When stock levels change (also emitted by sales)
        - low_stock_alert: When stock falls below minimum

        This module LISTENS to:
        - stock_changed: To check for low stock alerts

        This module provides HOOKS:
        - inventory.before_stock_change: Called before stock is modified
        - inventory.after_stock_change: Called after stock is modified
        - inventory.filter_product_data: Filter product data before save
        - inventory.filter_product_list: Filter product list queries

        This module provides SLOTS:
        - inventory.product_card_badge: Badge on product cards (stock, promo)
        - inventory.product_detail_tabs: Additional tabs in product detail
        - inventory.product_list_filters: Extra filters in product list
        - inventory.category_card_actions: Actions on category cards
        """
        self._register_signal_handlers()
        self._register_hooks()
        self._register_slots()

    def _register_signal_handlers(self):
        """Register handlers for signals."""
        from django.dispatch import receiver
        from apps.core.signals import stock_changed, low_stock_alert

        @receiver(stock_changed)
        def check_low_stock(sender, product_id, product_name, new_quantity, **kwargs):
            """
            Check if stock has fallen below minimum level.
            Emits low_stock_alert signal if needed.
            """
            from .models import Product

            try:
                product = Product.objects.get(id=product_id)
                min_stock = getattr(product, 'min_stock', 0) or 0

                if new_quantity <= min_stock:
                    low_stock_alert.send(
                        sender='inventory',
                        product=product,
                        current_stock=new_quantity,
                        minimum_stock=min_stock
                    )
            except Product.DoesNotExist:
                pass

    def _register_hooks(self):
        """
        Register hooks that this module OFFERS to other modules.

        Other modules can use these hooks to:
        - Validate stock changes before they happen
        - Modify product data before saving
        - Filter product listings
        """
        # Hooks are defined here but called from views/models
        # This method documents what hooks inventory offers
        pass

    def _register_slots(self):
        """
        Register slots that this module OFFERS to other modules.

        Slots are template injection points where other modules
        can add their content.
        """
        # Slots are defined in templates using {% render_slot %}
        # This method documents what slots inventory offers
        pass

    # =========================================================================
    # Hook Helper Methods (called from views)
    # =========================================================================

    @staticmethod
    def do_before_stock_change(product, old_quantity, new_quantity, reason, user=None):
        """
        Execute before_stock_change hook.

        Called by views before modifying stock. Other modules can:
        - Validate the change (raise ValidationError to block)
        - Log the change
        - Trigger notifications

        Args:
            product: Product instance
            old_quantity: Current stock level
            new_quantity: Proposed new stock level
            reason: Reason for change ('sale', 'adjustment', etc.)
            user: User making the change

        Raises:
            ValidationError: If a hook wants to block the change
        """
        from apps.core.hooks import hooks

        hooks.do_action(
            'inventory.before_stock_change',
            product=product,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            reason=reason,
            user=user
        )

    @staticmethod
    def do_after_stock_change(product, old_quantity, new_quantity, reason, user=None):
        """
        Execute after_stock_change hook.

        Called by views after stock has been modified. Other modules can:
        - Update their own data
        - Send notifications
        - Trigger reordering

        Args:
            product: Product instance
            old_quantity: Previous stock level
            new_quantity: New stock level
            reason: Reason for change
            user: User who made the change
        """
        from apps.core.hooks import hooks

        hooks.do_action(
            'inventory.after_stock_change',
            product=product,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            reason=reason,
            user=user
        )

    @staticmethod
    def filter_product_data(data, product=None, user=None):
        """
        Apply filter_product_data hook.

        Called before saving product data. Other modules can:
        - Add calculated fields
        - Validate data
        - Modify values

        Args:
            data: Dict of product data
            product: Existing product (None for new)
            user: User saving the product

        Returns:
            Modified data dict
        """
        from apps.core.hooks import hooks

        return hooks.apply_filters(
            'inventory.filter_product_data',
            data,
            product=product,
            user=user
        )

    @staticmethod
    def filter_product_list(queryset, filters=None, user=None):
        """
        Apply filter_product_list hook.

        Called when listing products. Other modules can:
        - Add additional filters
        - Exclude certain products
        - Annotate with extra data

        Args:
            queryset: Product queryset
            filters: Applied filters dict
            user: Requesting user

        Returns:
            Modified queryset
        """
        from apps.core.hooks import hooks

        return hooks.apply_filters(
            'inventory.filter_product_list',
            queryset,
            filters=filters,
            user=user
        )
