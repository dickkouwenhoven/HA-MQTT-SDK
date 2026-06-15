from ha_mqtt_sdk.models.device_info import DeviceInfo


def test_minimal_device_info():

    device: DeviceInfo = {
        "identifiers": [
            ("ha_mqtt_sdk", "device_1"),
        ],
    }

    assert device["identifiers"] == [
        ("ha_mqtt_sdk", "device_1"),
    ]


def test_full_device_info():

    device: DeviceInfo = {
        "identifiers": [
            ("ha_mqtt_sdk", "device_1"),
        ],
        "manufacturer": "IKEA",
        "model": "Dirigera",
        "name": "Bridge",
        "sw_version": "1.0.0",
        "hw_version": "A1",
        "suggested_area": "Living Room",
        "connections": [
            ("mac", "AA:BB:CC:DD:EE:FF"),
        ],
        "via_device": (
            "ha_mqtt_sdk",
            "gateway",
        ),
        "configuration_url": "http://192.168.1.10",
        "serial_number": "123456",
        "model_id": "DIRIGERA-001",
    }

    assert device["manufacturer"] == "IKEA"
    assert device["model"] == "Dirigera"
    assert device["name"] == "Bridge"
    assert device["serial_number"] == "123456"


def test_device_info_connections():

    device: DeviceInfo = {
        "identifiers": [
            ("ha_mqtt_sdk", "device_1"),
        ],
        "connections": [
            ("mac", "AA:BB:CC:DD:EE:FF"),
            ("zigbee", "00124B0012345678"),
        ],
    }

    assert len(device["connections"]) == 2


def test_device_info_via_device():

    device: DeviceInfo = {
        "identifiers": [
            ("ha_mqtt_sdk", "device_1"),
        ],
        "via_device": (
            "ha_mqtt_sdk",
            "gateway",
        ),
    }

    assert device["via_device"] == (
        "ha_mqtt_sdk",
        "gateway",
    )


def test_device_info_configuration_url():

    device: DeviceInfo = {
        "identifiers": [
            ("ha_mqtt_sdk", "device_1"),
        ],
        "configuration_url": "http://192.168.1.10",
    }

    assert device["configuration_url"] == "http://192.168.1.10"
