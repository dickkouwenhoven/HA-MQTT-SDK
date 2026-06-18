import pytest

from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.exceptions import EntityError, SchemaError
from ha_mqtt_sdk.models.entity import Entity


def test_to_dict_with_device_info()
    device_info: DeviceInfo = {}

    device_info["manufacturer"] = "Ikea"
    
    entity = Entity(
        domain=HADomain.SWITCH,
        name="Relay",
        unique_id="relay_1",
        device_info=device_info,
    )

    assert entity.to_dict() is not None
