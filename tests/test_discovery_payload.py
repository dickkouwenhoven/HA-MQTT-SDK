from ha_mqtt_sdk.builders.discovery_payload import build_discovery_payload
from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.models.entity import Entity


def test_basic_payload(mqtt_settings: MQTTSettings):
	entity = Entity(
		domain = HADomain.SENSOR,
		name = "Temp",
		unique_id = "temp_1",
	)

	payload = build_discovery_payload(
		entity,
		mqtt_settings.discovery_prefix,
	)

	assert payload["name"] == "Temp"
	assert payload["unique_id"] == "temp_1"

def test_payload_contains_state_topic(
	mqtt_settings: MQTTSettings,
):
	entity = Entity(
		domain = HADomain.SENSOR,
		name = "Temp",
		unique_id = "temp_1",
	)

	payload = build_discovery_payload(
		entity,
		mqtt_settings.discovery_prefix,
	)

	assert "state_topic" in payload

def test_payload_contains_command_topic(
	mqtt_settings: MQTTSettings,
):
	entity = Entity(
		domain = HADomain.SENSOR,
		name = "Temp",
		unique_id = "temp_1",
	)

	payload = build_discovery_payload(
		entity,
		mqtt_settings.discovery_prefix,
	)

	assert "command_topic"in payload

def test_payload_contains_device_block(
	mqtt_settings: MQTTSettings,
):
	entity = Entity(
		domain = HADomain.SENSOR,
		name = "Temp",
		unique_id = "temp_1",
		device_info={
			"identifiers": [
				("ha_mqtt_sdk", "device_1")
			],
			"manufacturer": "Example",
		},
	)

	payload = build_discovery_payload(
		entity,
		mqtt_settings.discovery_prefix,
	)

	assert "device"in payload

def test_payload_contains_extra_fields(
	mqtt_settings: MQTTSettings,
):
	entity = Entity(
		domain=HADomain.SENSOR,
		name="Temp",
		unique_id="temp_1",
		extra={
			"device_class": "temperature",
		},
	)
	
	payload = build_discovery_payload(
		entity,
		mqtt_settings.discovery_prefix,
	)
	
	assert payload["device_class"] == "temperature"

def test_payload_contains_all_sections(
	mqtt_settings: MQTTSettings,
):
	entity = Entity(
		domain=HADomain.SENSOR,
		name="Temp",
		unique_id="temp_1",
		device_info={
			"identifiers": [
				("ha_mqtt_sdk", "device_1")
			],
		},
		extra={
			"device_class": "temperature",
		},
	)
	
	payload = build_discovery_payload(
		entity,
		mqtt_settings.discovery_prefix,
	)
	
	assert "state_topic" in payload
	assert "command_topic" in payload
	assert "device" in payload
	assert payload["device_class"] == "temperature"

def test_payload_keeps_state_topic_after_build(
	mqtt_settings: MQTTSettings,
):
	entity = Entity(
		domain=HADomain.SENSOR,
		name="Temp",
		unique_id="temp_1",
	)
	payload = build_discovery_payload(
		entity,
		mqtt_settings.discovery_prefix,
	)
	required_fields = {
		"name",
		"unique_id",
		"state_topic",
		"command_topic",
	}
	
	assert required_fields.issubset(payload.keys())
