from unittest.mock import MagicMock, patch

from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.core.entity_factory import EntityRegistration, build_registration, create_entity

# ------------------------------------------------------------------
# create_entity
# ------------------------------------------------------------------


def test_create_entity():
    entity = create_entity(
        domain=HADomain.SENSOR,
        name="Temperature",
        unique_id="temp_1",
    )

    assert entity.domain == HADomain.SENSOR
    assert entity.name == "Temperature"
    assert entity.unique_id == "temp_1"


@patch("ha_mqtt_sdk.core.entity_factory.Entity.validate")
def test_create_entity_calls_validate(
    mock_validate,
):
    create_entity(
        domain=HADomain.SENSOR,
        name="Temperature",
        unique_id="temp_1",
    )

    mock_validate.assert_called_once()


def test_create_entity_with_optional_fields():
    device_info = {
        "identifiers": [("device_1", "sensor")],
        "manufacturer": "Test",
    }

    extra = {
        "unit_of_measurement": "°C",
    }

    entity = create_entity(
        domain=HADomain.SENSOR,
        name="Temperature",
        unique_id="temp_1",
        device_info=device_info,
        extra=extra,
    )

    assert entity.device_info == device_info
    assert entity.extra == extra


# ------------------------------------------------------------------
# build_registration
# ------------------------------------------------------------------


@patch("ha_mqtt_sdk.core.entity_factory.build_availability_topic")
@patch("ha_mqtt_sdk.builders.topic_manager.build_command_topic")
@patch("ha_mqtt_sdk.core.entity_factory.build_state_topic")
@patch("ha_mqtt_sdk.core.entity_factory.build_discovery_payload")
@patch("ha_mqtt_sdk.core.entity_factory.build_discovery_topic")
def test_build_registration(
    mock_discovery_topic,
    mock_discovery_payload,
    mock_state_topic,
    mock_command_topic,
    mock_availability_topic,
):

    entity = create_entity(
        domain=HADomain.SWITCH,
        name="Temperature",
        unique_id="temp_1",
    )

    mock_discovery_topic.return_value = "homeassistant/sensor/test/config"

    mock_discovery_payload.return_value = {"name": "Temperature"}

    mock_state_topic.return_value = "homeassistant/sensor/test/state"

    mock_command_topic.return_value = "homeassistant/sensor/test/set"

    mock_availability_topic.return_value = "homeassistant/sensor/test/availability"

    registration = build_registration(
        entity,
        "homeassistant",
    )

    assert isinstance(
        registration,
        EntityRegistration,
    )

    assert registration.discovery_topic == "homeassistant/sensor/test/config"

    assert registration.discovery_payload == {"name": "Temperature"}

    assert registration.state_topic == "homeassistant/sensor/test/state"

    assert registration.command_topic == "homeassistant/sensor/test/set"

    assert registration.availability_topic == "homeassistant/sensor/test/availability"


@patch("ha_mqtt_sdk.core.entity_factory.build_availability_topic")
@patch("ha_mqtt_sdk.builders.topic_manager.build_command_topic")
@patch("ha_mqtt_sdk.core.entity_factory.build_state_topic")
@patch("ha_mqtt_sdk.core.entity_factory.build_discovery_payload")
@patch("ha_mqtt_sdk.core.entity_factory.build_discovery_topic")
def test_build_registration_calls_dependencies_no_command_topic(
    mock_discovery_topic,
    mock_discovery_payload,
    mock_state_topic,
    mock_command_topic,
    mock_availability_topic,
):
    entity = MagicMock()

    entity.domain = HADomain.SENSOR
    entity.unique_id = "temp_1"

    build_registration(
        entity,
        "homeassistant",
    )

    entity.validate.assert_called_once()

    mock_discovery_topic.assert_called_once_with(
        entity.domain,
        entity.unique_id,
        "homeassistant",
    )

    mock_discovery_payload.assert_called_once_with(
        entity,
        "homeassistant",
    )

    mock_state_topic.assert_called_once_with(
        entity.domain,
        entity.unique_id,
        "homeassistant",
    )

    mock_command_topic.assert_not_called()

    mock_availability_topic.assert_called_once_with(
        entity.domain,
        entity.unique_id,
        "homeassistant",
    )


@patch("ha_mqtt_sdk.core.entity_factory.build_availability_topic")
@patch("ha_mqtt_sdk.builders.topic_manager.build_command_topic")
@patch("ha_mqtt_sdk.core.entity_factory.build_state_topic")
@patch("ha_mqtt_sdk.core.entity_factory.build_discovery_payload")
@patch("ha_mqtt_sdk.core.entity_factory.build_discovery_topic")
def test_build_registration_calls_dependencies_with_command_topic(
    mock_discovery_topic,
    mock_discovery_payload,
    mock_state_topic,
    mock_command_topic,
    mock_availability_topic,
):
    entity = MagicMock()

    entity.domain = HADomain.SWITCH
    entity.unique_id = "temp_1"

    build_registration(
        entity,
        "homeassistant",
    )

    entity.validate.assert_called_once()

    mock_discovery_topic.assert_called_once_with(
        entity.domain,
        entity.unique_id,
        "homeassistant",
    )

    mock_discovery_payload.assert_called_once_with(
        entity,
        "homeassistant",
    )

    mock_state_topic.assert_called_once_with(
        entity.domain,
        entity.unique_id,
        "homeassistant",
    )

    mock_command_topic.assert_called_once_with(
        entity.domain,
        entity.unique_id,
        "homeassistant",
    )

    mock_availability_topic.assert_called_once_with(
        entity.domain,
        entity.unique_id,
        "homeassistant",
    )


def test_entity_registration_dataclass():
    registration = EntityRegistration(
        discovery_topic="config",
        discovery_payload={"name": "test"},
        state_topic="state",
        command_topic="command",
        availability_topic="availability",
    )

    assert registration.discovery_topic == "config"
    assert registration.discovery_payload == {"name": "test"}
    assert registration.state_topic == "state"
    assert registration.command_topic == "command"
    assert registration.availability_topic == "availability"
