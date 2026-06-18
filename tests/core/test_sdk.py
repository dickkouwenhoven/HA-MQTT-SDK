import pytest

from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.core.entity_factory import create_entity
from ha_mqtt_sdk.core.sdk import HASDK
from ha_mqtt_sdk.exceptions import SDKError
from ha_mqtt_sdk.models.entity import Entity
from ha_mqtt_sdk.mqtt.paho_client import PahoMQTTClient

# -------------------------
# Init tests
# -------------------------


def test_init_requires_either_settings_or_client():
    with pytest.raises(SDKError):
        HASDK(mqtt_client=None, mqtt_settings=None)


def test_register_with_invalid_entity():
    with pytest.raises(SDKError):
        HASDK.register("Invalid Entity", "command_callback")


def test_update_state_with_invalid_entity():
    mqtt_config = MQTTSettings(
        host="localhost",
        port=1883,
    )

    client = PahoMQTTClient(config=mqtt_config)

    sdk = HASDK(
        mqtt_client=client,
    )

    with pytest.raises(SDKError):
        sdk.update_state("Invalid Entity", "ON")


def test_on_command_with_invalid_entity():
    mqtt_config = MQTTSettings(
        host="localhost",
        port=1883,
    )

    client = PahoMQTTClient(config=mqtt_config)

    sdk = HASDK(
        mqtt_client=client,
    )

    entity: Entity = create_entity(
        domain=HADomain.SWITCH,
        name="Relay",
        unique_id="relay_1",
    )

    entity.domain = "Invalid Domain"

    with pytest.raises(SDKError):
        sdk.on_command(entity, "command_callback")
