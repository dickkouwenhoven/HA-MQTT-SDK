from unittest.mock import MagicMock, patch

import pytest

from ha_mqtt_sdk.core.sdk import HASDK
from ha_mqtt_sdk.exceptions import SDKError

# -------------------------
# Helpers (fake objects)
# -------------------------


class FakeEntity:
    """Minimal stand-in for Entity."""
    pass


class FakeSettings:
    """Minimal stand-in for MQTTSettings."""
    pass


# -------------------------
# Init tests
# -------------------------


def test_init_requires_either_settings_or_client():
    with pytest.raises(SDKError):
        HASDK(mqtt_client=None, mqtt_settings=None)


@patch("src.ha_mqtt_sdk.core.sdk.PahoMQTTClient")
@patch("src.ha_mqtt_sdk.core.sdk.EntityManager")
def test_init_with_mqtt_settings_only(mock_entity_manager, mock_mqtt_client):
    settings = FakeSettings()

    HASDK(mqtt_client=None, mqtt_settings=settings)

    mock_mqtt_client.assert_called_once_with(settings)
    mock_entity_manager.assert_called_once()


@patch("src.ha_mqtt_sdk.core.sdk.EntityManager")
def test_init_with_mqtt_client_only(mock_entity_manager):
    mqtt_client = MagicMock()

    sdk = HASDK(mqtt_client=mqtt_client, mqtt_settings=None)

    assert sdk._mqtt is mqtt_client
    mock_entity_manager.assert_called_once()


@patch("src.ha_mqtt_sdk.core.sdk.get_logger")
@patch("src.ha_mqtt_sdk.core.sdk.EntityManager")
@patch("src.ha_mqtt_sdk.core.sdk.PahoMQTTClient")
def test_init_both_provided_warns(mock_mqtt_client, mock_entity_manager, mock_logger):
    logger = MagicMock()
    mock_logger.return_value = logger

    mqtt_client = MagicMock()
    settings = FakeSettings()

    HASDK(mqtt_client=mqtt_client, mqtt_settings=settings)

    logger.warning.assert_called_once()


# -------------------------
# Lifecycle tests
# -------------------------


@patch("src.ha_mqtt_sdk.core.sdk.EntityManager")
def test_start_and_shutdown(mock_entity_manager):
    mqtt_client = MagicMock()
    sdk = HASDK(mqtt_client=mqtt_client, mqtt_settings=FakeSettings())

    sdk.start()
    mqtt_client.connect.assert_called_once()

    sdk.shutdown()
    mqtt_client.disconnect.assert_called_once()


# -------------------------
# register
# -------------------------


@patch("src.ha_mqtt_sdk.core.sdk.EntityManager")
def test_register_valid_entity_delegates(mock_entity_manager):
    entity_manager = MagicMock()
    mock_entity_manager.return_value = entity_manager

    sdk = HASDK(mqtt_client=MagicMock(), mqtt_settings=FakeSettings())

    entity = FakeEntity()
    cb = MagicMock()

    sdk.register(entity, cb)

    entity_manager.register.assert_called_once_with(entity, cb)


def test_register_invalid_entity_raises():
    sdk = HASDK(mqtt_client=MagicMock(), mqtt_settings=FakeSettings())

    with pytest.raises(SDKError):
        sdk.register("not-an-entity")


# -------------------------
# update_state
# -------------------------


def test_update_state_invalid_entity_raises():
    sdk = HASDK(mqtt_client=MagicMock(), mqtt_settings=FakeSettings())

    with pytest.raises(SDKError):
        sdk.update_state("not-an-entity", "state")


@patch("src.ha_mqtt_sdk.core.sdk.EntityManager")
def test_update_state_delegates(mock_entity_manager):
    entity_manager = MagicMock()
    mock_entity_manager.return_value = entity_manager

    sdk = HASDK(mqtt_client=MagicMock(), mqtt_settings=FakeSettings())

    entity = FakeEntity()
    sdk.update_state(entity, {"on": True})

    entity_manager.update_state.assert_called_once_with(entity, {"on": True})


# -------------------------
# on_command
# -------------------------


def test_on_command_invalid_entity():
    sdk = HASDK(mqtt_client=MagicMock(), mqtt_settings=FakeSettings())

    with pytest.raises(SDKError):
        sdk.on_command("bad", lambda x, y: None)


def test_on_command_non_callable():
    sdk = HASDK(mqtt_client=MagicMock(), mqtt_settings=FakeSettings())

    entity = FakeEntity()

    with pytest.raises(SDKError):
        sdk.on_command(entity, "not-callable")


@patch("src.ha_mqtt_sdk.core.sdk.EntityManager")
def test_on_command_delegates(mock_entity_manager):
    entity_manager = MagicMock()
    mock_entity_manager.return_value = entity_manager

    sdk = HASDK(mqtt_client=MagicMock(), mqtt_settings=FakeSettings())

    entity = FakeEntity()
    cb = MagicMock()

    sdk.on_command(entity, cb)

    entity_manager.set_command_callback.assert_called_once_with(entity, cb)


# -------------------------
# create_entity
# -------------------------


@patch("src.ha_mqtt_sdk.core.sdk.EntityManager")
def test_create_entity_delegates(mock_entity_manager):
    entity_manager = MagicMock()
    expected_entity = FakeEntity()
    entity_manager.create_entity.return_value = expected_entity
    mock_entity_manager.return_value = entity_manager

    sdk = HASDK(mqtt_client=MagicMock(), mqtt_settings=FakeSettings())

    result = sdk.create_entity(
        domain="light",
        name="Lamp",
        unique_id="123",
        device_info=None,
        extra={"foo": "bar"},
    )

    assert result == expected_entity
    entity_manager.create_entity.assert_called_once()


# -------------------------
# unregister / is_registered
# -------------------------


@patch("src.ha_mqtt_sdk.core.sdk.EntityManager")
def test_unregister_and_is_registered(mock_entity_manager):
    entity_manager = MagicMock()
    entity_manager.is_registered.return_value = True
    mock_entity_manager.return_value = entity_manager

    sdk = HASDK(mqtt_client=MagicMock(), mqtt_settings=FakeSettings())
    entity = FakeEntity()

    sdk.unregister(entity)
    entity_manager.unregister.assert_called_once_with(entity)

    assert sdk.is_registered(entity) is True
    entity_manager.is_registered.assert_called_once_with(entity)
