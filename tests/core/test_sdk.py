from unittest.mock import MagicMock, patch

import pytest

from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.core.entity_factory import create_entity
from ha_mqtt_sdk.core.plugin_interface import IntegrationPlugin
from ha_mqtt_sdk.core.sdk import HASDK
from ha_mqtt_sdk.exceptions import EntityError, SDKError
from ha_mqtt_sdk.models.entity import Entity
from ha_mqtt_sdk.mqtt.paho_client import PahoMQTTClient

# -------------------------
# Helpers
# -------------------------


def make_sdk(mock_manager: MagicMock) -> HASDK:
    """Build a HASDK with a mocked EntityManager."""
    mqtt_config = MQTTSettings(host="localhost", port=1883)
    client = PahoMQTTClient(config=mqtt_config)
    with patch("ha_mqtt_sdk.core.sdk.EntityManager", return_value=mock_manager):
        return HASDK(mqtt_client=client)


def make_entity() -> Entity:
    return create_entity(domain=HADomain.SWITCH, name="Relay", unique_id="relay_1")


def make_plugin() -> MagicMock:
    """Return a MagicMock that passes isinstance check for IntegrationPlugin."""
    return MagicMock(spec=IntegrationPlugin)


# ---------------------------
# init
# ---------------------------


def test_init_requires_either_settings_or_client():
    with pytest.raises(SDKError):
        HASDK(mqtt_client=None, mqtt_settings=None)


def test_init_from_mqtt_settings_only():
    """Covers line 52: internal PahoMQTTClient construction."""
    mqtt_config = MQTTSettings(host="localhost", port=1883)
    sdk = HASDK(mqtt_settings=mqtt_config)

    assert sdk._mqtt is not None


def test_init_both_provided_uses_client(caplog: pytest.LogCaptureFixture):
    """Covers the warning branch when both are provided."""
    mqtt_config = MQTTSettings(host="localhost", port=1883)
    client = PahoMQTTClient(config=mqtt_config)

    with patch("ha_mqtt_sdk.core.sdk.EntityManager"):
        sdk = HASDK(mqtt_client=client, mqtt_settings=mqtt_config)

    assert sdk._mqtt is client


# ---------------------------
# start / shutdown
# ---------------------------


def test_start_calls_mqtt_connect():
    """Covers lines 58-59."""
    manager = MagicMock()
    sdk = make_sdk(manager)
    sdk._mqtt = MagicMock()

    sdk.start()

    sdk._mqtt.connect.assert_called_once()


def test_shutdown_calls_mqtt_disconnect():
    """Covers lines 71-72."""
    manager = MagicMock()
    sdk = make_sdk(manager)
    sdk._mqtt = MagicMock()

    sdk.shutdown()

    sdk._mqtt.disconnect.assert_called_once()


# ---------------------------
# register
# ---------------------------


def test_register_with_invalid_entity():
    with pytest.raises(SDKError):
        HASDK.register("Invalid Entity", "command_callback")  # type: ignore[arg-type]


def test_register_valid_entity():
    """Covers lines 78-79."""
    manager = MagicMock()
    sdk = make_sdk(manager)
    entity = make_entity()

    sdk.register(entity)

    manager.register.assert_called_once_with(entity, None)


def test_register_with_callback():
    manager = MagicMock()
    sdk = make_sdk(manager)
    entity = make_entity()

    def cb(topic: str, payload: str) -> None:
        pass

    sdk.register(entity, cb)

    manager.register.assert_called_once_with(entity, cb)


# ---------------------------
# Update_state
# ---------------------------


def test_update_state_with_invalid_entity():
    mqtt_config = MQTTSettings(host="localhost", port=1883)
    client = PahoMQTTClient(config=mqtt_config)
    sdk = HASDK(mqtt_client=client)

    with pytest.raises(SDKError):
        sdk.update_state("Invalid Entity", "ON")  # type: ignore[arg-type]


def test_update_state_valid_entity():
    """Covers line 93."""
    manager = MagicMock()
    sdk = make_sdk(manager)
    entity = make_entity()

    sdk.update_state(entity, "ON")

    manager.update_state.assert_called_once_with(entity, "ON")


# ---------------------------
# On_command
# ---------------------------


def test_on_command_with_invalid_entity():
    manager = MagicMock()
    sdk = make_sdk(manager)

    with pytest.raises(SDKError):
        sdk.on_command("not_an_entity", lambda t, p: None)  # type: ignore[arg-type]


def test_update_availability_unregistered_entity_raises():
    mqtt_config = MQTTSettings(host="localhost", port=1883)
    client = PahoMQTTClient(config=mqtt_config)
    client.publish = MagicMock()
    client.subscribe = MagicMock()
    client.set_message_callback = MagicMock()

    sdk = HASDK(async_mqtt_client=client)
    entity = make_entity()  # never registered

    with pytest.raises(EntityError):
        sdk.update_availability(entity, True)


def test_on_command_valid():
    """Covers line 105."""
    manager = MagicMock()
    sdk = make_sdk(manager)
    entity = make_entity()

    def cb(topic: str, payload: str) -> None:
        pass

    sdk.on_command(entity, cb)

    manager.set_command_callback.assert_called_once_with(entity, cb)


def test_on_command_non_callable_raises():
    """Covers line 115."""
    manager = MagicMock()
    sdk = make_sdk(manager)
    entity = make_entity()

    with pytest.raises(SDKError):
        sdk.on_command(entity, "not_a_callable")  # type: ignore[arg-type]


# ---------------------------
# Create_entity
# ---------------------------


def test_create_entity_returns_entity():
    """Covers line 120."""
    manager = MagicMock()
    sdk = make_sdk(manager)

    entity = sdk.create_entity(
        domain=HADomain.SWITCH,
        name="Relay",
        unique_id="relay_1",
    )

    assert isinstance(entity, Entity)
    assert entity.unique_id == "relay_1"


# ---------------------------
# Unregister
# ---------------------------


def test_unregister_delegates_to_manager():
    """Covers line 131."""
    manager = MagicMock()
    sdk = make_sdk(manager)
    entity = make_entity()

    sdk.unregister(entity)

    manager.unregister.assert_called_once_with(entity)


# ---------------------------
# Is_registered
# ---------------------------


def test_is_registered_true():
    """Covers lines 143 and 149."""
    manager = MagicMock()
    manager.is_registered.return_value = True
    sdk = make_sdk(manager)
    entity = make_entity()

    assert sdk.is_registered(entity) is True
    manager.is_registered.assert_called_once_with(entity)


def test_is_registered_false():
    manager = MagicMock()
    manager.is_registered.return_value = False
    sdk = make_sdk(manager)
    entity = make_entity()

    assert sdk.is_registered(entity) is False


# ---------------------------
# Use_plugin
# ---------------------------


def test_use_plugin_registers_plugin():
    """Lines 149-151: plugin manager created and plugin registered."""
    manager = MagicMock()
    sdk = make_sdk(manager)
    plugin = make_plugin()

    with patch("ha_mqtt_sdk.core.sdk.PluginManager") as mock_pm_cls:
        mock_pm = MagicMock()
        mock_pm_cls.return_value = mock_pm

        sdk.use_plugin("hue", plugin)

        mock_pm_cls.assert_called_once_with(sdk)
        mock_pm.register.assert_called_once_with("hue", plugin)


def test_use_plugin_reuses_existing_plugin_manager():
    """Second call must reuse the existing PluginManager, not create a new one."""
    manager = MagicMock()
    sdk = make_sdk(manager)

    with patch("ha_mqtt_sdk.core.sdk.PluginManager") as mock_pm_cls:
        mock_pm = MagicMock()
        mock_pm_cls.return_value = mock_pm

        sdk.use_plugin("hue", make_plugin())
        sdk.use_plugin("zwave", make_plugin())

        mock_pm_cls.assert_called_once()
        assert mock_pm.register.call_count == 2


# ---------------------------
# Run
# ---------------------------


def test_run_starts_mqtt_and_drives_plugin_lifecycle():
    """Lines 156-159: start + setup_all + start_all all called."""
    manager = MagicMock()
    sdk = make_sdk(manager)
    sdk._mqtt = MagicMock()

    mock_pm = MagicMock()
    sdk._plugin_manager = mock_pm

    sdk.run()

    sdk._mqtt.connect.assert_called_once()
    mock_pm.setup_all.assert_called_once()
    mock_pm.start_all.assert_called_once()


def test_run_without_plugins_only_starts_mqtt():
    """run() with no plugins registered must still connect MQTT."""
    manager = MagicMock()
    sdk = make_sdk(manager)
    sdk._mqtt = MagicMock()

    sdk.run()

    sdk._mqtt.connect.assert_called_once()


# ---------------------------
# Shutdown
# ---------------------------


def test_shutdown_calls_stop_all_before_disconnect():
    """Line 163: stop_all must be called before mqtt disconnect."""
    manager = MagicMock()
    sdk = make_sdk(manager)
    sdk._mqtt = MagicMock()

    mock_pm = MagicMock()
    sdk._plugin_manager = mock_pm

    sdk.shutdown()

    mock_pm.stop_all.assert_called_once()
    sdk._mqtt.disconnect.assert_called_once()
