from ha_mqtt_sdk.config.device_fields import (
    ALLOWED_FIELDS_PER_DOMAIN,
    COMMAND_FIELDS,
    COMMON_FIELDS,
    STATE_FIELDS,
    _optional,
)
from ha_mqtt_sdk.config.domains import HADomain


def test_optional_without_required():
    base = {"a", "b", "c"}
    extra = {"c", "d"}

    result = _optional(base, extra)

    assert result == {"a", "b", "c", "d"}


def test_optional_with_required():
    base = {"a", "b", "c"}
    extra = {"c", "d"}
    required = {"c"}

    result = _optional(base, extra, required=required)

    # 'c' must be removed due to required
    assert result == {"a", "b", "d"}


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


def test_light_accepts_modern_ha_schema_fields():
    """
    HA's MQTT light integration has two schemas: the legacy one (one
    dedicated command/state topic per capability) and the modern one
    introduced in HA 2021.x (a single topic, capabilities declared via
    supported_color_modes). Both must be accepted, since real
    integrations (e.g. DirigeraApi) use the modern schema.
    """
    optional = ALLOWED_FIELDS_PER_DOMAIN[HADomain.LIGHT]["optional"]

    for field in ("schema", "supported_color_modes", "min_mireds", "max_mireds"):
        assert field in optional, f"LIGHT is missing modern schema field {field!r}"


def test_light_still_accepts_legacy_schema_fields():
    """The legacy per-capability topic fields must still be accepted —
    this is an additive fix, not a replacement."""
    optional = ALLOWED_FIELDS_PER_DOMAIN[HADomain.LIGHT]["optional"]

    for field in (
        "brightness_command_topic",
        "brightness_state_topic",
        "color_temp_command_topic",
        "color_temp_state_topic",
        "hs_command_topic",
        "hs_state_topic",
        "rgb_command_topic",
        "rgb_state_topic",
        "xy_command_topic",
        "xy_state_topic",
    ):
    assert field in optional, f"LIGHT lost legacy schema field {field!r}"
