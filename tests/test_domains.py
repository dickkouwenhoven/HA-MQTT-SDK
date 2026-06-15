import pytest

from ha_mqtt_sdk.config.domains import HADomain


@pytest.mark.parametrize(
    "value",
    (member.value for member in HADomain],
)
def test_has_value_return_true_for_enum_values(value):
    assert HADomain.has_value(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "invalid",
        "",
        "sensor ",
        " Sensor",
        "SENSOR",
    ],
)
def test_has_value_returns_false_for_invalid_values(value):
    assert HADomain.has_value(value) is False
