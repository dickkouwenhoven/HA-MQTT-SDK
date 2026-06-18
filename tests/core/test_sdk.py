import pytest

from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.core.entity_factory import create_entity
from ha_mqtt_sdk.core.sdk import HASDK
from ha_mqtt_sdk.exceptions import SDKError
from ha_mqtt_sdk.models.entity import Entity

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
    with pytest.raises(SDKError):
        HASDK.update_state("Invalid Entity", "ON")


def test_on_command_with_invalid_entity():
    entity: Entity = create_entity(
        domain=HADomain.SWITCH,
        name="Relay",
        unique_id="relay_1",
    )

    callback = "command_callback"

    entity.domain = "Invalid Domain"
    with pytest.raises(SDKError):
        HASDK.on_command(entity, callback)
