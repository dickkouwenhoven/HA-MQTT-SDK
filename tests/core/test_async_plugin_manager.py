"""
Tests for core/async_plugin_manager.py

Verifies that AsyncPluginManager:
- Registers and retrieves plugins correctly
- Enforces no duplicate names
- Enforces correct plugin type
- Drives the full async lifecycle: setup_all, start_all, stop_all
- Catches and logs errors in stop_all without propagating
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ha_mqtt_sdk.core.async_plugin_interface import AsyncIntegrationPlugin
from ha_mqtt_sdk.core.async_plugin_manager import AsyncPluginManager
from ha_mqtt_sdk.exceptions import PluginError

# ── helpers ───────────────────────────────────────────────────────────────────


def make_plugin() -> MagicMock:
    """Return an AsyncMock that passes isinstance(plugin, AsyncIntegrationPlugin)."""
    plugin = MagicMock(spec=AsyncIntegrationPlugin)
    plugin.setup = AsyncMock()
    plugin.start = AsyncMock()
    plugin.stop = AsyncMock()
    plugin.handle_command = AsyncMock()
    return plugin


def make_manager() -> tuple[AsyncPluginManager, MagicMock]:
    sdk = MagicMock()
    return AsyncPluginManager(sdk), sdk


# ── register ──────────────────────────────────────────────────────────────────


def test_register_stores_plugin():
    manager, _ = make_manager()
    plugin = make_plugin()

    manager.register("dirigera", plugin)

    assert manager.get("dirigera") is plugin


def test_register_duplicate_name_raises():
    manager, _ = make_manager()

    manager.register("dirigera", make_plugin())

    with pytest.raises(PluginError, match="already registered"):
        manager.register("dirigera", make_plugin())


def test_register_invalid_type_raises():
    manager, _ = make_manager()

    with pytest.raises(PluginError):
        manager.register("dirigera", "not_a_plugin")  # type: ignore[arg-type]


# ── get ───────────────────────────────────────────────────────────────────────


def test_get_unknown_name_raises():
    manager, _ = make_manager()

    with pytest.raises(KeyError, match="dirigera"):
        manager.get("dirigera")


# ── setup_all ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_setup_all_calls_setup_on_each_plugin():
    manager, sdk = make_manager()
    plugin_a = make_plugin()
    plugin_b = make_plugin()

    manager.register("a", plugin_a)
    manager.register("b", plugin_b)

    await manager.setup_all()

    plugin_a.setup.assert_awaited_once_with(sdk)
    plugin_b.setup.assert_awaited_once_with(sdk)


@pytest.mark.asyncio
async def test_setup_all_preserves_registration_order():
    manager, _ = make_manager()
    call_order: list[str] = []

    plugin_a = make_plugin()
    plugin_b = make_plugin()
    plugin_a.setup.side_effect = lambda s: call_order.append("a")
    plugin_b.setup.side_effect = lambda s: call_order.append("b")

    manager.register("a", plugin_a)
    manager.register("b", plugin_b)
    await manager.setup_all()

    assert call_order == ["a", "b"]


# ── start_all ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_all_calls_start_on_each_plugin():
    manager, _ = make_manager()
    plugin_a = make_plugin()
    plugin_b = make_plugin()

    manager.register("a", plugin_a)
    manager.register("b", plugin_b)

    await manager.start_all()

    plugin_a.start.assert_awaited_once()
    plugin_b.start.assert_awaited_once()


# ── stop_all ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stop_all_calls_stop_on_each_plugin():
    manager, _ = make_manager()
    plugin_a = make_plugin()
    plugin_b = make_plugin()

    manager.register("a", plugin_a)
    manager.register("b", plugin_b)

    await manager.stop_all()

    plugin_a.stop.assert_awaited_once()
    plugin_b.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_stop_all_continues_after_plugin_error():
    """Error in one plugin must not prevent others from stopping."""
    manager, _ = make_manager()
    plugin_a = make_plugin()
    plugin_b = make_plugin()

    plugin_a.stop.side_effect = RuntimeError("boom")

    manager.register("a", plugin_a)
    manager.register("b", plugin_b)

    await manager.stop_all()  # must not raise

    plugin_b.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_stop_all_logs_error_on_failure():
    manager, _ = make_manager()
    plugin = make_plugin()
    plugin.stop.side_effect = RuntimeError("crash")

    manager.register("failing", plugin)

    with patch("ha_mqtt_sdk.core.async_plugin_manager._logger") as mock_logger:
        await manager.stop_all()

    mock_logger.error.assert_called_once()
    assert "failing" in mock_logger.error.call_args[0][1]


# ── no plugins registered ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_setup_all_with_no_plugins():
    manager, _ = make_manager()
    await manager.setup_all()  # must not raise


@pytest.mark.asyncio
async def test_start_all_with_no_plugins():
    manager, _ = make_manager()
    await manager.start_all()  # must not raise


@pytest.mark.asyncio
async def test_stop_all_with_no_plugins():
    manager, _ = make_manager()
    await manager.stop_all()  # must not raise
