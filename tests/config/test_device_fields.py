from ha_mqtt_sdk.config.device_fields import (
    ALLOWED_FIELDS_PER_DOMAIN,
    COMMAND_FIELDS,
    COMMON_FIELDS,
    STATE_FIELDS,
)
from ha_mqtt_sdk.config.domains import HADomain


def test_all_domains_have_configuration():
    assert set(ALLOWED_FIELDS_PER_DOMAIN.keys()) == set(HADomain)


def test_domain_configuration_structure():
    for config in ALLOWED_FIELDS_PER_DOMAIN.values():
        assert "required" in config
        assert "optional" in config

        assert isinstance(config["required"], set)
        assert isinstance(config["optional"], set)


def test_required_and_optional_do_not_overlap():
    for domain, config in ALLOWED_FIELDS_PER_DOMAIN.items():
        overlap = config["required"] & config["optional"]

        assert overlap == set(), f"{domain}: required and optional overlap: {overlap}"

def test_sensor_required_fields():
    config = ALLOWED_FIELDS_PER_DOMAIN[HADomain.SENSOR]

    assert config["required"] == {
        "name",
        "state_topic",
        "unique_id",
    }


def test_switch_required_fields():
    config = ALLOWED_FIELDS_PER_DOMAIN[HADomain.SWITCH]

    assert config["required"] == {
        "name",
        "command_topic",
        "unique_id",
    }


def test_common_fields_contains_expected_fields():
    assert "device" in COMMON_FIELDS
    assert "availability_topic" in COMMON_FIELDS
    assert "qos" in COMMON_FIELDS


def test_state_fields_contains_expected_fields():
    assert "state_topic" in STATE_FIELDS
    assert "expire_after" in STATE_FIELDS


def test_command_fields_contains_expected_fields():
    assert "command_topic" in COMMAND_FIELDS
    assert "payload_on" in COMMAND_FIELDS
    assert "payload_off" in COMMAND_FIELDS
