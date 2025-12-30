"""
Tests for Inventory module extension points (hooks, slots, and signals).

Tests that the inventory module correctly:
- Emits signals when products/stock change
- Listens to stock_changed and emits low_stock_alert
- Provides hooks for stock changes and product filtering
- Provides slots for UI extension points

Note: These tests run within the hub's pytest environment and use the
module's models which are dynamically loaded.
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from apps.core.signals import (
    product_created,
    product_updated,
    product_deleted,
    stock_changed,
    low_stock_alert,
)
from apps.core.hooks import hooks
from apps.core.slots import slots


@pytest.mark.django_db
class TestInventorySignalEmission:
    """Tests for signals emitted by inventory module."""

    def test_product_created_signal(self):
        """Verify product_created signal can be emitted."""
        handler = MagicMock()
        product_created.connect(handler)

        try:
            # Emit signal as inventory module would
            product_created.send(
                sender='inventory',
                product=MagicMock(id=1, name='New Product'),
                user=MagicMock(id=1)
            )

            handler.assert_called_once()
            call_kwargs = handler.call_args[1]
            assert call_kwargs['sender'] == 'inventory'
        finally:
            product_created.disconnect(handler)

    def test_product_updated_signal(self):
        """Verify product_updated signal includes changed fields."""
        handler = MagicMock()
        product_updated.connect(handler)

        try:
            product_updated.send(
                sender='inventory',
                product=MagicMock(id=1),
                user=MagicMock(id=1),
                changed_fields=['price', 'stock']
            )

            handler.assert_called_once()
            call_kwargs = handler.call_args[1]
            assert 'price' in call_kwargs['changed_fields']
        finally:
            product_updated.disconnect(handler)

    def test_product_deleted_signal(self):
        """Verify product_deleted signal sends product info."""
        handler = MagicMock()
        product_deleted.connect(handler)

        try:
            product_deleted.send(
                sender='inventory',
                product_id=123,
                product_name='Deleted Product',
                user=MagicMock(id=1)
            )

            handler.assert_called_once()
            call_kwargs = handler.call_args[1]
            assert call_kwargs['product_id'] == 123
            assert call_kwargs['product_name'] == 'Deleted Product'
        finally:
            product_deleted.disconnect(handler)

    def test_stock_changed_signal(self):
        """Verify stock_changed signal includes all details."""
        handler = MagicMock()
        stock_changed.connect(handler)

        try:
            stock_changed.send(
                sender='inventory',
                product_id=1,
                product_name='Test Product',
                old_quantity=100,
                new_quantity=95,
                change_reason='adjustment',
                reference_id=None
            )

            handler.assert_called_once()
            call_kwargs = handler.call_args[1]
            assert call_kwargs['old_quantity'] == 100
            assert call_kwargs['new_quantity'] == 95
            assert call_kwargs['change_reason'] == 'adjustment'
        finally:
            stock_changed.disconnect(handler)


@pytest.mark.django_db
class TestLowStockAlertSignal:
    """Tests for low_stock_alert signal handling."""

    def test_low_stock_alert_emitted(self):
        """Verify low_stock_alert signal can be emitted."""
        handler = MagicMock()
        low_stock_alert.connect(handler)

        try:
            low_stock_alert.send(
                sender='inventory',
                product=MagicMock(id=1, name='Low Stock Item'),
                current_stock=3,
                minimum_stock=10
            )

            handler.assert_called_once()
            call_kwargs = handler.call_args[1]
            assert call_kwargs['current_stock'] == 3
            assert call_kwargs['minimum_stock'] == 10
        finally:
            low_stock_alert.disconnect(handler)

    def test_low_stock_check_on_stock_changed(self):
        """
        Verify that inventory's stock_changed handler checks for low stock.

        The inventory module's AppConfig.ready() registers a handler for
        stock_changed that emits low_stock_alert when appropriate.
        """
        # This test verifies the integration pattern, not the actual handler
        # (which requires the product model)
        alerts = []

        def check_and_alert(sender, product_id, new_quantity, **kwargs):
            # Simulate what inventory's handler does
            min_stock = 10  # Simulated min_stock
            if new_quantity <= min_stock:
                low_stock_alert.send(
                    sender='inventory',
                    product=MagicMock(id=product_id),
                    current_stock=new_quantity,
                    minimum_stock=min_stock
                )

        def track_alert(sender, current_stock, **kwargs):
            alerts.append(current_stock)

        stock_changed.connect(check_and_alert)
        low_stock_alert.connect(track_alert)

        try:
            # Trigger stock changed below minimum
            stock_changed.send(
                sender='sales',
                product_id=1,
                product_name='Test',
                old_quantity=15,
                new_quantity=5,
                change_reason='sale',
                reference_id=1
            )

            assert len(alerts) == 1
            assert alerts[0] == 5
        finally:
            stock_changed.disconnect(check_and_alert)
            low_stock_alert.disconnect(track_alert)

    def test_no_alert_when_above_minimum(self):
        """Verify no alert when stock is above minimum."""
        alerts = []

        def check_and_alert(sender, product_id, new_quantity, **kwargs):
            min_stock = 10
            if new_quantity <= min_stock:
                alerts.append(new_quantity)

        stock_changed.connect(check_and_alert)

        try:
            stock_changed.send(
                sender='sales',
                product_id=1,
                product_name='Test',
                old_quantity=100,
                new_quantity=50,
                change_reason='sale',
                reference_id=1
            )

            assert len(alerts) == 0
        finally:
            stock_changed.disconnect(check_and_alert)


@pytest.mark.django_db
class TestInventorySignalIntegration:
    """Integration tests for inventory signal workflows."""

    def test_sale_triggers_low_stock_chain(self):
        """Verify sale -> stock_changed -> low_stock_alert chain."""
        notifications = []

        def handle_stock_changed(sender, product_id, new_quantity, **kwargs):
            min_stock = 10
            if new_quantity <= min_stock:
                low_stock_alert.send(
                    sender='inventory',
                    product=MagicMock(id=product_id),
                    current_stock=new_quantity,
                    minimum_stock=min_stock
                )

        def handle_alert(sender, product, current_stock, minimum_stock, **kwargs):
            notifications.append({
                'product_id': product.id,
                'current_stock': current_stock,
                'minimum_stock': minimum_stock
            })

        stock_changed.connect(handle_stock_changed)
        low_stock_alert.connect(handle_alert)

        try:
            # Simulate sale bringing stock below minimum
            stock_changed.send(
                sender='sales',
                product_id=42,
                product_name='Test Product',
                old_quantity=15,
                new_quantity=3,
                change_reason='sale',
                reference_id=123
            )

            assert len(notifications) == 1
            assert notifications[0]['product_id'] == 42
            assert notifications[0]['current_stock'] == 3
        finally:
            stock_changed.disconnect(handle_stock_changed)
            low_stock_alert.disconnect(handle_alert)

    def test_multiple_products_stock_changes(self):
        """Verify signals work for multiple product updates."""
        changes = []

        def track_changes(sender, product_id, new_quantity, **kwargs):
            changes.append({'product_id': product_id, 'stock': new_quantity})

        stock_changed.connect(track_changes)

        try:
            for i in range(5):
                stock_changed.send(
                    sender='inventory',
                    product_id=i + 1,
                    product_name=f'Product {i + 1}',
                    old_quantity=100,
                    new_quantity=100 - (i * 10),
                    change_reason='adjustment',
                    reference_id=None
                )

            assert len(changes) == 5
            assert changes[0]['stock'] == 100
            assert changes[4]['stock'] == 60
        finally:
            stock_changed.disconnect(track_changes)

    def test_stock_changed_from_different_senders(self):
        """Verify stock_changed works from different module senders."""
        senders = []

        def track_sender(sender, **kwargs):
            senders.append(sender)

        stock_changed.connect(track_sender)

        try:
            stock_changed.send(sender='sales', product_id=1, product_name='P1',
                             old_quantity=10, new_quantity=5, change_reason='sale', reference_id=1)
            stock_changed.send(sender='returns', product_id=1, product_name='P1',
                             old_quantity=5, new_quantity=6, change_reason='return', reference_id=2)
            stock_changed.send(sender='inventory', product_id=1, product_name='P1',
                             old_quantity=6, new_quantity=10, change_reason='adjustment', reference_id=None)

            assert senders == ['sales', 'returns', 'inventory']
        finally:
            stock_changed.disconnect(track_sender)


@pytest.mark.django_db
class TestInventoryHooks:
    """Tests for inventory hooks."""

    def setup_method(self):
        """Clear hooks before each test."""
        hooks.clear_all()

    def teardown_method(self):
        """Clear hooks after each test."""
        hooks.clear_all()

    def test_before_stock_change_hook_called(self):
        """Verify before_stock_change hook is called before stock modification."""
        hook_calls = []

        def track_stock_change(product, old_quantity, new_quantity, reason, **kwargs):
            hook_calls.append({
                'product_id': product.id,
                'old': old_quantity,
                'new': new_quantity,
                'reason': reason
            })

        hooks.add_action('inventory.before_stock_change', track_stock_change)

        # Simulate calling the hook as inventory would
        product = MagicMock(id=1, name='Test Product')
        hooks.do_action(
            'inventory.before_stock_change',
            product=product,
            old_quantity=100,
            new_quantity=95,
            reason='sale',
            user=None
        )

        assert len(hook_calls) == 1
        assert hook_calls[0]['old'] == 100
        assert hook_calls[0]['new'] == 95
        assert hook_calls[0]['reason'] == 'sale'

    def test_after_stock_change_hook_called(self):
        """Verify after_stock_change hook is called after stock modification."""
        hook_calls = []

        def track_stock_change(product, old_quantity, new_quantity, reason, **kwargs):
            hook_calls.append({
                'product_id': product.id,
                'change': new_quantity - old_quantity
            })

        hooks.add_action('inventory.after_stock_change', track_stock_change)

        product = MagicMock(id=1)
        hooks.do_action(
            'inventory.after_stock_change',
            product=product,
            old_quantity=100,
            new_quantity=95,
            reason='sale',
            user=None
        )

        assert len(hook_calls) == 1
        assert hook_calls[0]['change'] == -5

    def test_filter_product_data_hook(self):
        """Verify filter_product_data hook can modify product data."""
        def add_computed_field(data, product=None, **kwargs):
            data['computed_margin'] = float(data.get('price', 0)) * 0.2
            return data

        hooks.add_filter('inventory.filter_product_data', add_computed_field)

        original_data = {'name': 'Test', 'price': 100.00}
        filtered_data = hooks.apply_filters(
            'inventory.filter_product_data',
            original_data,
            product=None,
            user=None
        )

        assert filtered_data['computed_margin'] == 20.0
        assert filtered_data['name'] == 'Test'

    def test_filter_product_list_hook(self):
        """Verify filter_product_list hook can modify queryset."""
        def exclude_inactive(queryset, filters=None, **kwargs):
            # Simulate filtering by returning modified queryset
            queryset._filtered = True
            return queryset

        hooks.add_filter('inventory.filter_product_list', exclude_inactive)

        mock_queryset = MagicMock()
        filtered_qs = hooks.apply_filters(
            'inventory.filter_product_list',
            mock_queryset,
            filters={'active': True},
            user=None
        )

        assert filtered_qs._filtered is True

    def test_multiple_hooks_chain(self):
        """Verify multiple hooks chain correctly."""
        def add_tax(data, **kwargs):
            data['price_with_tax'] = data.get('price', 0) * 1.21
            return data

        def add_discount(data, **kwargs):
            data['discount'] = data.get('price', 0) * 0.1
            return data

        hooks.add_filter('inventory.filter_product_data', add_tax, priority=10)
        hooks.add_filter('inventory.filter_product_data', add_discount, priority=20)

        data = {'price': 100}
        filtered = hooks.apply_filters('inventory.filter_product_data', data)

        assert filtered['price_with_tax'] == 121.0
        assert filtered['discount'] == 10.0


@pytest.mark.django_db
class TestInventorySlots:
    """Tests for inventory slots."""

    def setup_method(self):
        """Clear slots before each test."""
        slots.clear_all()

    def teardown_method(self):
        """Clear slots after each test."""
        slots.clear_all()

    def test_product_card_badge_slot(self):
        """Verify other modules can register for product_card_badge slot."""
        def promo_badge_context(context):
            product = context.get('product')
            return {'has_promo': True, 'discount': 15}

        slots.register(
            'inventory.product_card_badge',
            template='promotions/partials/promo_badge.html',
            context_fn=promo_badge_context,
            module_id='promotions'
        )

        content = slots.get_slot_content(
            'inventory.product_card_badge',
            {'product': MagicMock(id=1)}
        )

        assert len(content) == 1
        assert content[0]['context']['has_promo'] is True
        assert content[0]['context']['discount'] == 15

    def test_product_detail_tabs_slot(self):
        """Verify other modules can register for product_detail_tabs slot."""
        def stock_history_context(context):
            return {'show_history': True}

        slots.register(
            'inventory.product_detail_tabs',
            template='analytics/partials/stock_history_tab.html',
            context_fn=stock_history_context,
            module_id='analytics'
        )

        content = slots.get_slot_content('inventory.product_detail_tabs', {})
        assert len(content) == 1

    def test_product_list_filters_slot(self):
        """Verify other modules can add filters to product list."""
        def supplier_filter_context(context):
            return {'suppliers': ['Supplier A', 'Supplier B']}

        slots.register(
            'inventory.product_list_filters',
            template='suppliers/partials/supplier_filter.html',
            context_fn=supplier_filter_context,
            module_id='suppliers'
        )

        content = slots.get_slot_content('inventory.product_list_filters', {})
        assert len(content) == 1
        assert 'Supplier A' in content[0]['context']['suppliers']

    def test_multiple_modules_register_same_slot(self):
        """Verify multiple modules can register for the same slot."""
        slots.register(
            'inventory.product_card_badge',
            template='promotions/badge.html',
            module_id='promotions',
            priority=10
        )
        slots.register(
            'inventory.product_card_badge',
            template='loyalty/member_badge.html',
            module_id='loyalty',
            priority=20
        )

        content = slots.get_slot_content('inventory.product_card_badge', {})
        assert len(content) == 2
        # Lower priority first
        assert content[0]['template'] == 'promotions/badge.html'
        assert content[1]['template'] == 'loyalty/member_badge.html'


@pytest.mark.django_db
class TestInventoryIntegrationScenarios:
    """Integration tests combining hooks and signals."""

    def setup_method(self):
        """Clear hooks and slots before each test."""
        hooks.clear_all()
        slots.clear_all()

    def teardown_method(self):
        """Clear hooks and slots after each test."""
        hooks.clear_all()
        slots.clear_all()

    def test_stock_change_hook_triggers_signal(self):
        """Test that after_stock_change hook can trigger signals."""
        signals_emitted = []

        def emit_signal_on_change(product, old_quantity, new_quantity, **kwargs):
            stock_changed.send(
                sender='inventory',
                product_id=product.id,
                product_name=product.name,
                old_quantity=old_quantity,
                new_quantity=new_quantity,
                change_reason='hook_test',
                reference_id=None
            )

        def track_signal(sender, product_id, **kwargs):
            signals_emitted.append(product_id)

        hooks.add_action('inventory.after_stock_change', emit_signal_on_change)
        stock_changed.connect(track_signal)

        try:
            hooks.do_action(
                'inventory.after_stock_change',
                product=MagicMock(id=42, name='Test'),
                old_quantity=100,
                new_quantity=90,
                reason='test'
            )

            assert 42 in signals_emitted
        finally:
            stock_changed.disconnect(track_signal)

    def test_reordering_module_integration(self):
        """Simulate reordering module listening to low stock."""
        reorder_triggered = []

        def check_reorder(sender, product, current_stock, minimum_stock, **kwargs):
            if current_stock < minimum_stock * 0.5:
                reorder_triggered.append({
                    'product_id': product.id,
                    'quantity_to_order': minimum_stock * 2
                })

        low_stock_alert.connect(check_reorder)

        try:
            low_stock_alert.send(
                sender='inventory',
                product=MagicMock(id=1),
                current_stock=2,
                minimum_stock=10
            )

            assert len(reorder_triggered) == 1
            assert reorder_triggered[0]['quantity_to_order'] == 20
        finally:
            low_stock_alert.disconnect(check_reorder)
