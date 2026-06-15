from unittest.mock import MagicMock

import pytest

from ha_mqtt_sdk.models.entity import Entity
from ha_mqtt_sdk.plugin_interface import IntegrationPlugin

# -------------------------------------------------
# 1. ABC cannot be instantiated
# -------------------------------------------------


def test_integration_plugin_cannot_be_instantiated():
    with pytest.raises(TypeError):
        IntegrationPlugin()


# -------------------------------------------------
# 2. Fake implementation for testing contract
# -------------------------------------------------


class FakePlugin(IntegrationPlugin):
    def map_device(self, data, entity_manager):
        return [Entity(domain="sensor", unique_id="test", name="Test")]

    def handle_command(self, topic, payload):
        return f"{topic}:{payload}"


# -------------------------------------------------
# 3. Contract behavior tests
# -------------------------------------------------


def test_fake_plugin_map_device_returns_entities():
    plugin = FakePlugin()

    entity_manager = MagicMock()
    result = plugin.map_device({"device": "x"}, entity_manager)

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], Entity)
    assert result[0].unique_id == "test"


def test_fake_plugin_handle_command_returns_expected_string():
    plugin = FakePlugin()

    result = plugin.handle_command("test/topic", "ON")

    assert result == "test/topic:ON"


# -------------------------------------------------
# 4. Ensure abstract methods are enforced
# -------------------------------------------------


def test_missing_method_implementation_raises_error():
    class BrokenPlugin(IntegrationPlugin):
        def map_device(self, data, entity_manager):
            return []

        # handle_command ontbreekt bewust

    with pytest.raises(TypeError):
        BrokenPlugin()


# -----------------------------
# 1. ABC mag niet geïnstantieerd worden
# -----------------------------


def test_cannot_instantiate_abstract_class():
    with pytest.raises(TypeError):
        IntegrationPlugin()


# -----------------------------
# 2. Subclass zonder implementatie faalt
# -----------------------------


def test_missing_implementation_raises_typeerror():
    class BadPlugin(IntegrationPlugin):
        pass

    with pytest.raises(TypeError):
        BadPlugin()


# -----------------------------
# 3. Partial implementation faalt ook
# -----------------------------


def test_partial_implementation_raises_typeerror():
    class BadPlugin(IntegrationPlugin):
        def map_device(self, data, entity_manager):
            return []

    with pytest.raises(TypeError):
        BadPlugin()


# -----------------------------
# 4. Volledige implementatie werkt
# -----------------------------


def test_valid_plugin_can_be_instantiated():
    class GoodPlugin(IntegrationPlugin):
        def map_device(self, data, entity_manager):
            return []

        def handle_command(self, topic, payload):
            return None

    plugin = GoodPlugin()

    assert isinstance(plugin, IntegrationPlugin)


# -----------------------------
# 5. Methoden zijn callable
# -----------------------------


def test_plugin_methods_work():
    class GoodPlugin(IntegrationPlugin):
        def map_device(self, data, entity_manager):
            return ["entity"]

        def handle_command(self, topic, payload):
            return None

    plugin = GoodPlugin()

    result = plugin.map_device({}, object())
    assert result == ["entity"]

    # mag gewoon None returnen
    assert plugin.handle_command("topic", {"a": 1}) is None
