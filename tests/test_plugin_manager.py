import pytest

from unittest.mock import MagicMock

from ha_mqtt_sdk.plugin_interface import IntegrationPlugin
from ha_mqtt_sdk.plugin_manager import PluginManager

# -------------------------------------------------
# Helpers
# -------------------------------------------------

@pytest.fixture
def plugin_manager():
    return PluginManager()


@pytest.fixture
def mock_plugin():
    return MagicMock(spec=IntegrationPlugin)


# -------------------------------------------------
# Tests
# -------------------------------------------------

def test_register_plugin_stores_plugin(plugin_manager, mock_plugin):
    plugin_manager.register_plugin("hue", mock_plugin)

    assert "hue" in plugin_manager._plugins
    assert plugin_manager._plugins["hue"] is mock_plugin


def test_get_plugin_returns_registered_plugin(plugin_manager, mock_plugin):
    plugin_manager.register_plugin("hue", mock_plugin)

    result = plugin_manager.get_plugin("hue")

    assert result is mock_plugin


def test_get_plugin_unknown_key_raises_keyerror(plugin_manager):
    with pytest.raises(KeyError):
        plugin_manager.get_plugin("non_existing")


def test_multiple_plugins_are_isolated(plugin_manager):
    plugin_a = MagicMock(spec=IntegrationPlugin)
    plugin_b = MagicMock(spec=IntegrationPlugin)

    plugin_manager.register_plugin("a", plugin_a)
    plugin_manager.register_plugin("b", plugin_b)

    assert plugin_manager.get_plugin("a") is plugin_a
    assert plugin_manager.get_plugin("b") is plugin_b


def test_register_overwrites_plugin(plugin_manager):
    plugin1 = MagicMock(spec=IntegrationPlugin)
    plugin2 = MagicMock(spec=IntegrationPlugin)

    plugin_manager.register_plugin("hue", plugin1)
    plugin_manager.register_plugin("hue", plugin2)

    assert plugin_manager.get_plugin("hue") is plugin2
