from ha-mqtt-sdk.builders.topic_manager import (
	build_state_topic,
	build_command_topic,
	build_discovery_topic,
	build_availability_topic,
)
from sdk.config.domains import HADomain

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
	topic = build_availibity_topic(
                HADomain.SENSOR,
                "id1",
                "homeassistant",
        )
        assert topic.endswith("/availability"

def test_discovery_topic():
	topic = build_discovery_topic(
                HADomain.SENSOR,
                "id1",
                "homeassistant",
        )
        assert "config" in topic




