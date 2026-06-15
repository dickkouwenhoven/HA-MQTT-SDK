import pytest

from ha_mqtt_sdk.core.device_factory import create_device_info
from ha_mqtt_sdk.models.device_info import DeviceInfo


def test_create_device_info_empty():
    device_info: DeviceInfo = create_device_info()

    assert device_info == {}


def test_create_device_info_all_fields():
    identifiers = [("my_domain", "device_1")]
    connections = [("mac", "AA:BB:CC:DD:EE:FF")]
    via_device = ("my_domain", "gateway")

    device_info: DeviceInfo = create_device_info(
        identifiers=identifiers,
        connections=connections,
        manufacturer="Acme",
        model="Model X",
        name="Living Room Sensor",
        sw_version="1.0.0",
        hw_version="A1",
        suggested_area="Living Room",
        via_device=via_device,
        configuration_url="https://example.com",
        serial_number="123456",
        model_id="MODEL-X",
    )

    assert device_info == {
        "identifiers": identifiers,
        "connections": connections,
        "manufacturer": "Acme",
        "model": "Model X",
        "name": "Living Room Sensor",
        "sw_version": "1.0.0",
        "hw_version": "A1",
        "suggested_area": "Living Room",
        "via_device": via_device,
        "configuration_url": "https://example.com",
        "serial_number": "123456",
        "model_id": "MODEL-X",
    }


def test_create_device_info_omits_none_values():
    device_info = create_device_info(
        manufacturer="Acme",
        model=None,
        name="Sensor",
    )

    assert device_info == {
        "manufacturer": "Acme",
        "name": "Sensor",
    }

    assert "model" not in device_info


@pytest.mark.parametrize(
    ("kwargs", "expected_key", "expected_value"),
    [
        ({"identifiers": [("domain", "id")]}, "identifiers", [("domain", "id")]),
        ({"connections": [("mac", "AA:BB")]}, "connections", [("mac", "AA:BB")]),
        ({"manufacturer": "Acme"}, "manufacturer", "Acme"),
        ({"model": "Model X"}, "model", "Model X"),
        ({"name": "Sensor"}, "name", "Sensor"),
        ({"sw_version": "1.0"}, "sw_version", "1.0"),
        ({"hw_version": "A1"}, "hw_version", "A1"),
        ({"suggested_area": "Kitchen"}, "suggested_area", "Kitchen"),
        ({"via_device": ("domain", "gateway")}, "via_device", ("domain", "gateway")),
        ({"configuration_url": "https://example.com"}, "configuration_url", "https://example.com"),
        ({"serial_number": "123456"}, "serial_number", "123456"),
        ({"model_id": "MODEL-X"}, "model_id", "MODEL-X"),
    ],
)
def test_create_device_info_single_field(kwargs, expected_key, expected_value):
    device_info = create_device_info(**kwargs)

    assert device_info == {
        expected_key: expected_value,
    }


