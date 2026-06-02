import pytest
from ha_mqtt_sdk.models.entity import Entity
from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.exceptions import EntityError, SchemaError

def test_valid_entity():
	entity = Entity(
		domain = HADomain.SENSOR,
		name = "Temp",
		unique_id = "temp_1",
	)
	entity.validate()

def test_missing_name():
	with pytest.raises(EntityError):
		Entity(
			domain = HADomain.SENSOR,
			name = "",
			unique_id = "id",
		).validate()

def test_invalid_domain():
	with pytest.raises(EntityError):
		Entity(
			domain = "invalid",
			name = "Test",
			unique_id = "id",
		).validate()

def test_missing_unique_id():
	with pytest.raises(EntityError):
		Entity(
			domain=HADomain.SENSOR,
			name="Temp",
			unique_id="",
		).validate()

def test_invalid_extra_field():
	with pytest.raises(SchemaError):
		Entity(
			domain=HADomain.SENSOR,
			name="Temp",
			unique_id="temp_1",
			extra={
				"banana": "yellow",
			},
		).validate()

def test_valid_extra_field():
	Entity(
		domain=HADomain.SENSOR,
		name="Temp",
		unique_id="temp_1",
		extra={
			"device_class": "temperature",
		},
	).validate()

def test_invalid_device_info_type():
	with pytest.raises(EntityError):
		Entity(
			domain=HADomain.SENSOR,
			name="Temp",
			unique_id="temp_1",
			device_info="invalid",			
		).validate()

def test_valid_device_info():
	Entity(
		domain=HADomain.SENSOR,
		name="Temp",
		unique_id="temp_1",
		device_info={
			"identifiers": [
				("ha_mqtt_sdk", "device_1")
			],
			"manufacturer": "Example",
		},
	).validate()
	
def test_device_info_missing_identifiers():
	with pytest.raises(EntityError):
		Entity(
			domain=HADomain.SENSOR,
			name="Temp",
			unique_id="temp_1",
			device_info={},
		).validate()
