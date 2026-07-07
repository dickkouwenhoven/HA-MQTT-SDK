import pytest

from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.core.entity_factory import create_entity
from ha_mqtt_sdk.exceptions import EntityError, SchemaError
from ha_mqtt_sdk.models.entity import Entity

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------


def make_entity(**kwargs) -> Entity:
    defaults = dict(domain=HADomain.SENSOR, name="Temp", unique_id="temp_1")
    defaults.update(kwargs)
    return Entity(**defaults)


def make_switch(**kwargs) -> Entity:
    defaults = dict(domain=HADomain.SWITCH, name="Switch", unique_id="switch_1")
    defaults.update(kwargs)
    return Entity(**defaults)


# ── to_dict ───────────────────────────────────────────────────────────────────


def test_to_dict_without_device_info():
    """Line 62->65: no device_info — payload.update(extra) reached directly."""
    entity = make_entity(extra={"device_class": "temperature"})
    result = entity.to_dict()

    assert result["name"] == "Temp"
    assert result["unique_id"] == "temp_1"
    assert "device" not in result
    assert result["device_class"] == "temperature"


def test_to_dict_with_device_info():
    """Line 62-63: device_info included in payload."""
    device_info = {
        "manufacturer": "Ikea",
        "identifiers": [("relay_1", "ABC123")],
    }
    entity = create_entity(
        domain=HADomain.SWITCH,
        name="Relay",
        unique_id="relay_1",
        device_info=device_info,
    )
    result = entity.to_dict()

    assert result["device"] == device_info


# ── _validate_basic ───────────────────────────────────────────────────────────


def test_valid_entity():
    make_entity().validate()


def test_invalid_domain_raises():
    with pytest.raises(EntityError):
        Entity(domain="invalid", name="Test", unique_id="id").validate()


def test_empty_name_raises():
    with pytest.raises(EntityError):
        make_entity(name="").validate()


def test_empty_unique_id_raises():
    with pytest.raises(EntityError):
        make_entity(unique_id="").validate()


def test_extra_not_dict_raises():
    """Line 128: extra is truthy but not a dict."""
    entity = make_entity()
    entity.extra = "not_a_dict"  # type: ignore[assignment]

    with pytest.raises(EntityError):
        entity.validate()


# ── device_info basic validation ──────────────────────────────────────────────


def test_device_info_not_dict_raises():
    with pytest.raises(EntityError):
        make_entity(device_info="invalid").validate()  # type: ignore[arg-type]


def test_device_info_missing_identifiers_and_connections_raises():
    with pytest.raises(EntityError):
        make_entity(device_info={}).validate()


def test_valid_device_info_with_identifiers():
    make_entity(
        device_info={
            "identifiers": [("ha_mqtt_sdk", "device_1")],
            "manufacturer": "Example",
        }
    ).validate()


def test_valid_device_info_with_connections():
    make_entity(device_info={"connections": [("mac", "AA:BB:CC:DD:EE:FF")]}).validate()


# ── _validate_tuple_collection ────────────────────────────────────────────────


def test_identifiers_not_a_list_raises():
    """Line 79: identifiers is not a list."""
    with pytest.raises(EntityError):
        make_entity(device_info={"identifiers": ("ha_mqtt_sdk", "device_1")}).validate()


def test_identifiers_empty_list_raises():
    """Line 82: identifiers is an empty list."""
    with pytest.raises(EntityError):
        make_entity(device_info={"identifiers": []}).validate()


def test_identifiers_item_not_tuple_raises():
    """Line 86: item in identifiers is not a tuple."""
    with pytest.raises(EntityError):
        make_entity(device_info={"identifiers": ["not_a_tuple"]}).validate()


def test_identifiers_tuple_wrong_length_raises():
    """Line 86: tuple has wrong length."""
    with pytest.raises(EntityError):
        make_entity(device_info={"identifiers": [("only_one",)]}).validate()


def test_identifiers_key_empty_raises():
    """Line 91: tuple key is empty string."""
    with pytest.raises(EntityError):
        make_entity(device_info={"identifiers": [("", "device_1")]}).validate()


def test_identifiers_key_not_string_raises():
    """Line 91: tuple key is not a string."""
    with pytest.raises(EntityError):
        make_entity(device_info={"identifiers": [(123, "device_1")]}).validate()


def test_identifiers_value_empty_raises():
    """Line 94: tuple value is empty string."""
    with pytest.raises(EntityError):
        make_entity(device_info={"identifiers": [("ha_mqtt_sdk", "")]}).validate()


def test_identifiers_value_not_string_raises():
    """Line 94: tuple value is not a string."""
    with pytest.raises(EntityError):
        make_entity(device_info={"identifiers": [("ha_mqtt_sdk", 123)]}).validate()


def test_connections_empty_list_raises():
    """Line 82 via connections path."""
    with pytest.raises(EntityError):
        make_entity(device_info={"connections": []}).validate()


# ── _validate_tuple_pair (via_device) ────────────────────────────────────────


def test_valid_via_device():
    make_entity(
        device_info={
            "identifiers": [("ha_mqtt_sdk", "device_1")],
            "via_device": ("ha_mqtt_sdk", "gateway_1"),
        }
    ).validate()


def test_via_device_not_tuple_raises():
    """Line 102: via_device is not a tuple."""
    with pytest.raises(EntityError):
        make_entity(
            device_info={
                "identifiers": [("ha_mqtt_sdk", "device_1")],
                "via_device": "not_a_tuple",
            }
        ).validate()


def test_via_device_wrong_length_raises():
    """Line 105: via_device tuple has wrong length."""
    with pytest.raises(EntityError):
        make_entity(
            device_info={
                "identifiers": [("ha_mqtt_sdk", "device_1")],
                "via_device": ("gateway_1",),
            }
        ).validate()


def test_via_device_key_empty_raises():
    """Line 110: via_device key is empty string."""
    with pytest.raises(EntityError):
        make_entity(
            device_info={
                "identifiers": [("ha_mqtt_sdk", "device_1")],
                "via_device": ("", "gateway_1"),
            }
        ).validate()


def test_via_device_value_empty_raises():
    """Line 113: via_device value is empty string."""
    with pytest.raises(EntityError):
        make_entity(
            device_info={
                "identifiers": [("ha_mqtt_sdk", "device_1")],
                "via_device": ("ha_mqtt_sdk", ""),
            }
        ).validate()


# ── string fields in device_info ──────────────────────────────────────────────


def test_device_info_string_field_not_string_raises():
    """Line 186: manufacturer is not a string."""
    with pytest.raises(EntityError):
        make_entity(
            device_info={
                "identifiers": [("ha_mqtt_sdk", "device_1")],
                "manufacturer": 123,  # type: ignore[typeddict-item]
            }
        ).validate()


def test_device_info_string_field_empty_raises():
    """Line 189: manufacturer is an empty string."""
    with pytest.raises(EntityError):
        make_entity(
            device_info={
                "identifiers": [("ha_mqtt_sdk", "device_1")],
                "manufacturer": "",
            }
        ).validate()


# ── _validate_schema ──────────────────────────────────────────────────────────


def test_invalid_extra_field_raises():
    with pytest.raises(SchemaError):
        make_entity(extra={"banana": "yellow"}).validate()


def test_valid_extra_field():
    make_entity(extra={"device_class": "temperature"}).validate()


# ── LIGHT domain — modern HA MQTT light schema ─────────────────────────────
#
# HA's MQTT light integration has a legacy schema (one dedicated
# command/state topic per capability) and a modern schema, introduced
# in HA 2021.x, that declares capabilities via supported_color_modes
# instead. Real integrations (e.g. DirigeraApi) use the modern schema
# — these tests cover the three capability tiers it actually produces.


def make_light(**kwargs) -> Entity:
    defaults = dict(domain=HADomain.LIGHT, name="Light", unique_id="light_1")
    defaults.update(kwargs)
    return Entity(**defaults)


def test_light_onoff_only_validates():
    make_light(extra={"supported_color_modes": ["onoff"]}).validate()


def test_light_dimmable_validates():
    make_light(extra={"brightness_scale": 100, "supported_color_modes": ["brightness"]}).validate()


def test_light_colour_temperature_validates():
    make_light(
        extra={
            "brightness_scale": 100,
            "supported_color_modes": ["color_temp"],
            "min_mireds": 250,
            "max_mireds": 454,
        }
    ).validate()


def test_light_full_colour_json_schema_validates():
    make_light(
        extra={
            "schema": "json",
            "supported_color_modes": ["hs", "color_temp"],
            "min_mireds": 250,
            "max_mireds": 454,
        }
    ).validate()


def test_light_legacy_schema_still_validates():
    """The old per-capability-topic schema must still work — this was
    an additive fix, not a replacement."""
    make_light(
        extra={
            "brightness_command_topic": "light/brightness/set",
            "brightness_state_topic": "light/brightness/state",
            "color_temp_command_topic": "light/color_temp/set",
            "color_temp_state_topic": "light/color_temp/state",
        }
    ).validate()


def test_unknown_domain_raises_schema_error():
    """Line 197: domain with no schema definition raises SchemaError."""
    entity = make_entity()
    entity.domain = HADomain.SENSOR

    # Patch the schema lookup to return nothing
    from unittest.mock import patch

    with (
        patch("ha_mqtt_sdk.models.entity.ALLOWED_FIELDS_PER_DOMAIN", {}),
        pytest.raises(SchemaError),
    ):
        entity.validate()
