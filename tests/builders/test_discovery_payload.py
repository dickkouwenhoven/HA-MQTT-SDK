from unittest.mock import patch

import pytest

from ha_mqtt_sdk.builders.discovery_payload import _validate_entity, build_discovery_payload
from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.exceptions import EntityError
from ha_mqtt_sdk.models.entity import Entity


def test_basic_payload(mqtt_settings: MQTTSettings):
    entity = Entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    payload = build_discovery_payload(
        entity,
        mqtt_settings.discovery_prefix,
    )

    assert payload["name"] == "Temp"
    assert payload["unique_id"] == "temp_1"


def test_payload_contains_state_topic(
    mqtt_settings: MQTTSettings,
):
    entity = Entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    payload = build_discovery_payload(
        entity,
        mqtt_settings.discovery_prefix,
    )

    assert "state_topic" in payload


def test_payload_contains_command_topic(
    mqtt_settings: MQTTSettings,
):
    entity = Entity(
        domain=HADomain.ALARM_CONTROL_PANEL,
        name="Temp",
        unique_id="temp_1",
    )

    payload = build_discovery_payload(
        entity,
        mqtt_settings.discovery_prefix,
    )

    assert "command_topic" in payload


def test_payload_contains_device_block(
    mqtt_settings: MQTTSettings,
):
    entity = Entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
        device_info={
            "identifiers": [("ha_mqtt_sdk", "device_1")],
            "manufacturer": "Example",
        },
    )

    payload = build_discovery_payload(
        entity,
        mqtt_settings.discovery_prefix,
    )

    assert "device" in payload


# ── device.identifiers / connections / via_device serialization ──────────────
#
# HA's MQTT discovery schema requires device.identifiers and
# device.via_device to be plain strings, not the SDK's internal
# list[tuple[str, str]] / tuple[str, str] representation. Sending the
# tuple form as-is makes HA reject the whole discovery payload with
# "value should be a string @ data['device']['identifiers'][0]" —
# a real failure this project hit against a live Home Assistant
# instance, which is why this needs direct coverage rather than just
# the "device" in payload check above.


def test_payload_flattens_device_identifiers(
    mqtt_settings: MQTTSettings,
):
    entity = Entity(
        domain=HADomain.SENSOR,
        name="Hub Firmware",
        unique_id="hub_1_firmware",
        device_info={
            "identifiers": [("dirigera", "9d3b17d8-73c0-4f33-9637-e8ee2437acd3")],
            "name": "Ikea Hub",
        },
    )

    payload = build_discovery_payload(entity, mqtt_settings.discovery_prefix)

    assert payload["device"]["identifiers"] == ["dirigera_9d3b17d8-73c0-4f33-9637-e8ee2437acd3"]
    assert all(isinstance(i, str) for i in payload["device"]["identifiers"])


def test_payload_preserves_device_connections_shape(
    mqtt_settings: MQTTSettings,
):
    """connections keeps its [[type, value], ...] pair shape — this is
    the shape HA actually expects, unlike identifiers/via_device."""
    entity = Entity(
        domain=HADomain.SENSOR,
        name="Hub",
        unique_id="hub_1",
        device_info={
            "identifiers": [("dirigera", "hub-id")],
            "connections": [("mac", "aa:bb:cc:dd:ee:ff")],
        },
    )

    payload = build_discovery_payload(entity, mqtt_settings.discovery_prefix)

    assert payload["device"]["connections"] == [["mac", "aa:bb:cc:dd:ee:ff"]]


def test_payload_flattens_via_device(
    mqtt_settings: MQTTSettings,
):
    entity = Entity(
        domain=HADomain.SENSOR,
        name="Child",
        unique_id="child_1",
        device_info={
            "identifiers": [("dirigera", "child-id")],
            "via_device": ("dirigera", "parent-id"),
        },
    )

    payload = build_discovery_payload(entity, mqtt_settings.discovery_prefix)

    assert payload["device"]["via_device"] == "dirigera_parent-id"
    assert isinstance(payload["device"]["via_device"], str)


def test_payload_device_block_without_optional_fields(
    mqtt_settings: MQTTSettings,
):
    """connections/via_device are optional (DeviceInfo has total=False)
    — must not crash when they're absent."""
    entity = Entity(
        domain=HADomain.SENSOR,
        name="Simple",
        unique_id="simple_1",
        device_info={
            "identifiers": [("dirigera", "simple-id")],
        },
    )

    payload = build_discovery_payload(entity, mqtt_settings.discovery_prefix)

    assert payload["device"]["identifiers"] == ["dirigera_simple-id"]
    assert "connections" not in payload["device"]
    assert "via_device" not in payload["device"]


def test_payload_contains_extra_fields(
    mqtt_settings: MQTTSettings,
):
    entity = Entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
        extra={
            "device_class": "temperature",
        },
    )

    payload = build_discovery_payload(
        entity,
        mqtt_settings.discovery_prefix,
    )

    assert payload["device_class"] == "temperature"


def test_payload_contains_all_sections(
    mqtt_settings: MQTTSettings,
):
    entity = Entity(
        domain=HADomain.ALARM_CONTROL_PANEL,
        name="Temp",
        unique_id="temp_1",
        device_info={
            "identifiers": [("ha_mqtt_sdk", "device_1")],
        },
        extra={
            "device_class": "temperature",
        },
    )

    payload = build_discovery_payload(
        entity,
        mqtt_settings.discovery_prefix,
    )

    assert "state_topic" in payload
    assert "command_topic" in payload
    assert "device" in payload
    assert payload["device_class"] == "temperature"


def test_payload_keeps_state_topic_after_build(
    mqtt_settings: MQTTSettings,
):
    entity = Entity(
        domain=HADomain.ALARM_CONTROL_PANEL,
        name="Temp",
        unique_id="temp_1",
    )
    payload = build_discovery_payload(
        entity,
        mqtt_settings.discovery_prefix,
    )
    required_fields = {
        "name",
        "unique_id",
        "state_topic",
        "command_topic",
    }

    assert required_fields.issubset(payload.keys())


def test_validate_entity_invalid_type_raises():
    with pytest.raises(EntityError):
        _validate_entity("not_an_entity")


def test_payload_without_state_topic(
    mqtt_settings: MQTTSettings,
):
    entity = Entity(
        domain=HADomain.BUTTON,
        name="Button",
        unique_id="button_1",
    )

    with patch(
        "ha_mqtt_sdk.builders.discovery_payload.build_state_topic",
        return_value=None,
    ):
        payload = build_discovery_payload(
            entity,
            mqtt_settings.discovery_prefix,
        )

    assert "state_topic" not in payload


def test_payload_device_with_connections_only(
    mqtt_settings: MQTTSettings,
):
    entity = Entity(
        domain=HADomain.SENSOR,
        name="Connection Device",
        unique_id="connection_device_1",
        device_info={
            "connections": [("mac", "aa:bb:cc:dd:ee:ff")],
        },
    )

    payload = build_discovery_payload(
        entity,
        mqtt_settings.discovery_prefix,
    )

    assert payload["device"]["connections"] == [["mac", "aa:bb:cc:dd:ee:ff"]]
    assert "identifiers" not in payload["device"]


def test_discovery_payload_includes_availability_topic():
    entity = Entity(
        domain=HADomain.SENSOR,
        name="Sensor",
        unqiue_id="sensor_1",
    )

    payload = build_discovery_payload(entity, prefix="homeassistant")

    assert "availability_topic" in payload
    assert payload["payload_available"] == "online"
    assert payload["payload_not_availabled"] == "offline"
