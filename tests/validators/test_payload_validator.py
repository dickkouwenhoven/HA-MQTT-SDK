import pytest

from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.exceptions import ValidationError
from ha_mqtt_sdk.validators.payload_validator import (
    validate_discovery_payload,
    validate_json_serializable,
)

# -------------------------
# validate_json_serializable
# -------------------------


def test_validate_json_serializable_valid_simple():
    validate_json_serializable(
        {
            "a": 1,
            "b": "text",
            "c": True,
            "d": None,
        }
    )


def test_validate_json_serializable_nested_valid():
    validate_json_serializable(
        {
            "a": [1, 2, {"b": "c"}],
            "d": (1, 2, 3),
        }
    )


def test_validate_json_serializable_invalid_type():
    class NotSerializable:
        pass

    with pytest.raises(ValidationError) as exc:
        validate_json_serializable({"a": NotSerializable()})

    assert "payload.a" in str(exc.value)


def test_validate_json_serializable_invalid_key_type():
    with pytest.raises(ValidationError) as exc:
        validate_json_serializable({1: "value"})

    assert "JSON object keys must be strings" in str(exc.value)


# -------------------------
# validate_discovery_payload
# -------------------------


def test_validate_discovery_payload_valid():
    payload = {
        "unique_id": "device-123",
        "name": "Test Device",
        "state_topic": "home/test",
    }

    validate_discovery_payload(payload, HADomain())


def test_validate_discovery_payload_not_mapping():
    with pytest.raises(ValidationError):
        validate_discovery_payload(["not", "a", "dict"], HADomain())


def test_validate_discovery_payload_empty():
    with pytest.raises(ValidationError):
        validate_discovery_payload({}, HADomain())


@pytest.mark.parametrize(
    "missing_field",
    ["unique_id", "name", "state_topic"],
)
def test_validate_discovery_payload_missing_required_fields(missing_field):
    payload = {
        "unique_id": "id",
        "name": "name",
        "state_topic": "topic",
    }
    payload.pop(missing_field)

    with pytest.raises(ValidationError) as exc:
        validate_discovery_payload(payload, HADomain())

    assert f"{missing_field}" in str(exc.value)


def test_validate_discovery_payload_state_topic_wrong_type():
    payload = {
        "unique_id": "id",
        "name": "name",
        "state_topic": 123,  # invalid
    }

    with pytest.raises(ValidationError) as exc:
        validate_discovery_payload(payload, HADomain())

    assert "state_topic must be a string" in str(exc.value)
