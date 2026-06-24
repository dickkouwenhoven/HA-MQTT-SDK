"""
Tests for core/plugin_manager.py

Verifies that PluginManager:
- Registers and retrieves plugins correctly
- Enforces no duplicate names
- Enforces correct plugin type
- Drives the full lifecycle: setup_all, start_all, stop_all
- Catches and logs errors in stop_all without propagating
"""

from unittest.mock import MagicMock, call, patch

import pytest

from ha_mqtt_sdk.core.plugin_interface import IntegrationPlugin
from ha_mqtt_sdk.core.plugin_manager import PluginManager


# ── helpers ───────────────────────────────────────────────────────────────────


def make_plugin() -> MagicMock:
    """Return a MagicMock that passes isinstance(plugin, IntegrationPlugin)."""
    plugin = MagicMock(spec=IntegrationPlugin)
    return plugin


def make_manager() -> tuple[PluginManager, MagicMock]:
    sdk = MagicMock()
    return PluginManager(sdk), sdk


# ── register ──────────────────────────────────────────────────────────────────


def test_register_stores_plugin():
    manager, _ = make_manager()
    plugin = make_plugin()

    manager.register("hue", plugin)

    assert manager.get("hue") is plugin


def test_register_duplicate_name_raises():
    manager, _ = make_manager()
    plugin = make_plugin()

    manager.register("hue", plugin)

    with pytest.raises(ValueError, match="already registered"):
        manager.register("hue", make_plugin())


def test_register_invalid_type_raises():
    manager, _ = make_manager()

    with pytest.raises(TypeError):
        manager.register("hue", "not_a_plugin")  # type: ignore[arg-type]


# ── get ───────────────────────────────────────────────────────────────────────


def test_get_unknown_name_raises():
    manager, _ = make_manager()

    with pytest.raises(KeyError, match="hue"):
        manager.get("hue")


# ── setup_all ─────────────────────────────────────────────────────────────────


def test_setup_all_calls_setup_on_each_plugin():
    manager, sdk = make_manager()
    plugin_a = make_plugin()
    plugin_b = make_plugin()

    manager.register("a", plugin_a)
    manager.register("b", plugin_b)

    manager.setup_all()

    plugin_a.setup.assert_called_once_with(sdk)
    plugin_b.setup.assert_called_once_with(sdk)


def test_setup_all_preserves_registration_order():
    manager, sdk = make_manager()
    call_order: list[str] = []

    plugin_a = MagicMock(spec=IntegrationPlugin)
    plugin_b = MagicMock(spec=IntegrationPlugin)
    plugin_a.setup.side_effect = lambda s: call_order.append("a")
    plugin_b.setup.side_effect = lambda s: call_order.append("b")

    manager.register("a", plugin_a)
    manager.register("b", plugin_b)
    manager.setup_all()

    assert call_order == ["a", "b"]


# ── start_all ─────────────────────────────────────────────────────────────────


def test_start_all_calls_start_on_each_plugin():
    manager, _ = make_manager()
    plugin_a = make_plugin()
    plugin_b = make_plugin()

    manager.register("a", plugin_a)
    manager.register("b", plugin_b)

    manager.start_all()

    plugin_a.start.assert_called_once()
    plugin_b.start.assert_called_once()


# ── stop_all ──────────────────────────────────────────────────────────────────


def test_stop_all_calls_stop_on_each_plugin():
    manager, _ = make_manager()
    plugin_a = make_plugin()
    plugin_b = make_plugin()

    manager.register("a", plugin_a)
    manager.register("b", plugin_b)

    manager.stop_all()

    plugin_a.stop.assert_called_once()
    plugin_b.stop.assert_called_once()


def test_stop_all_continues_after_plugin_error():
    """Error in one plugin must not prevent others from stopping."""
    manager, _ = make_manager()
    plugin_a = make_plugin()
    plugin_b = make_plugin()

    plugin_a.stop.side_effect = RuntimeError("boom")

    manager.register("a", plugin_a)
    manager.register("b", plugin_b)

    manager.stop_all()  # must not raise

    plugin_b.stop.assert_called_once()


def test_stop_all_logs_error_on_failure():
    manager, _ = make_manager()
    plugin = make_plugin()
    plugin.stop.side_effect = RuntimeError("crash")

    manager.register("failing", plugin)

    with patch("ha_mqtt_sdk.core.plugin_manager._logger") as mock_logger:
        manager.stop_all()

    mock_logger.error.assert_called_once()
    assert "failing" in mock_logger.error.call_args[0][1]


# ── no plugins registered ─────────────────────────────────────────────────────


def test_setup_all_with_no_plugins():
    manager, _ = make_manager()
    manager.setup_all()  # must not raise


def test_start_all_with_no_plugins():
    manager, _ = make_manager()
    manager.start_all()  # must not raise


def test_stop_all_with_no_plugins():
    manager, _ = make_manager()
    manager.stop_all()  # must not raise
