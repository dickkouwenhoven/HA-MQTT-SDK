import pytest

from unittest.mock import MagicMock

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
        return [Entity(entity_id="test", name="Test")]

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
    assert result[0].entity_id == "test"


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
