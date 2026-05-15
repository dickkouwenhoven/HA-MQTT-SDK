from ha_mqtt_sdk.builders.discovery_payload import build_discovery_payload
from ha_mqtt_sdk.models.entity import Entity
from ha_mqtt_sdk.config.domains import HADomain

def test_basic_payload(self):
	entity = Entity(
		domain = HADomain.SENSOR,
		name = "Temp",
		unique_id = "temp_1",
	)

	payload = build_discovery_payload(
		entity,
		self._settings.discovery_prefix,
	)

	assert payload["name"] == "Temp"
	assert payload["unique_id"] == "temp_1"
	
