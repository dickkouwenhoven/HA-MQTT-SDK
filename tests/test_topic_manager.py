import pytest

from ha_mqtt_sdk.builders.topic_manager import (
	build_state_topic,
	build_command_topic,
	build_discovery_topic,
	build_availability_topic,
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
	assert topic.endswith("/availability")

def test_discovery_topic():
	topic = build_discovery_topic(
                HADomain.SENSOR,
                "id1",
                "homeassistant",
        )
	assert "config" in topic

def test_sensor_has_no_command_topic():
	topic = build_command_topic(
		HADomain.SENSOR,
		"id1",
		"hoemassistant",
	)

	assert topic == ""

def test_invalid_domain):
	with pytest.raise(BuilderError):
		build_state_topic(
			"invalid",
			"id1",
			"homeassistant",
		)
