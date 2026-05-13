from ha_mqtt_sdk.builders.discovery_payload import build_discovery_payload
from ha_mqtt_sdk.models.entity import Entity
from ha_mqtt_sdk.config.domains import HADomain

def test_basic_payload():
	entity = Entity(
		domain = HADomain.SENSOR,
		name = "Temp",
		unique_id = "temp_1",
		state_topic = "topic/state",
	)

	payload = build_discovery_payload(entity)

	assert payload["name"] == "Temp"
	assert payload["unique_id"] == "temp_1"
	assert "state_topic" in payload

