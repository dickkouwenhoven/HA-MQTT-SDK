import pytest

from ha_mqtt_sdk.builders.topic_manager import (
    build_availability_topic,
    build_command_topic,
    build_discovery_topic,
    build_state_topic,
)
from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.exceptions import BuilderError


def test_state_topic():
    topic = build_state_topic(
        HADomain.SENSOR,
        "id1",
        "homeassistant",
    )
    assert topic == "homeassistant/sensor/id1/state"


def test_command_topic():
    topic = build_command_topic(
        HADomain.SWITCH,
        "id1",
        "homeassistant",
    )
    assert topic == "homeassistant/switch/id1/set"


def test_availability_topic():
    topic = build_availability_topic(
        HADomain.SENSOR,
        "id1",
        "homeassistant",
    )
    assert topic == (
        "homeassistant/sensor/id1/availability"
    )


def test_discovery_topic():
    topic = build_discovery_topic(
        HADomain.SENSOR,
        "id1",
        "homeassistant",
    )
    assert topic == (
        "homeassistant/sensor/id1/config"
    )


def test_sensor_has_no_command_topic():
    topic = build_command_topic(
        HADomain.SENSOR,
        "id1",
        "homeassistant",
    )

    assert topic == ""


def test_invalid_domain():
    with pytest.raises(BuilderError):
        build_state_topic(
            "invalid",
            "id1",
            "homeassistant",
        )


def test_empty_unique_id():
    with pytest.raise(BuilderError):
        build_state_topic(
            HADomain.SENSOR,
            "",
            "homeassistant",
        )


def test_empty_prefix():
    with pytest.raise(BuilderError):
        build_state_topic(
            HADomain.SENSOR,
            "id1",
            "",
        )

@pytest.mark.parametrize(
    "builder,expected",
    [
        (
            build_state_topic,
            "homeassistant/sensor/id1/state",
        ),
        (
            build_availability_topic,
            "homeassistant/sensor/id1/availability",
        ),
    ],
)
def test_topic_are_built_correctly(
    builder,
    expected,
):
    assert builder(
        HADomain.SENSOR,
        "id1",
        "homeassistant",
    ) == expected
     
