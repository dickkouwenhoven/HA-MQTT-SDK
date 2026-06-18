from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.core.entity_factory import create_entity
from ha_mqtt_sdk.models.device_info import DeviceInfo
from ha_mqtt_sdk.models.entity import Entity


def test_to_dict_with_device_info():
    device_info: DeviceInfo = {}

    device_info = {
        "manufacturer": "Ikea",
        "identifiers": "relay_1",
    }

    entity: Entity = create_entity(
        domain=HADomain.SWITCH,
        name="Relay",
        unique_id="relay_1",
        device_info=device_info,
    )

    assert entity.to_dict() is not None
