import pytest

from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.exceptions import EntityError, SchemaError
from ha_mqtt_sdk.models.entity import Entity


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
	
def test_device_info_missing_identifiers_and_connections():
	with pytest.raises(EntityError):
		Entity(
			domain=HADomain.SENSOR,
			name="Temp",
			unique_id="temp_1",
			device_info={},
		).validate()

def test_device_info_identifier_not_tuple():
	with pytest.raises(EntityError):
		Entity(
			domain=HADomain.SENSOR,
			name="Temp",
			unique_id="temp_1",
			device_info={
				"identifiers": ["abc"]
			}
		).validate()
		
def test_device_info_empty_identifiers():
	with pytest.raises(EntityError):
		Entity(
			domain=HADomain.SENSOR,
			name="Temp",
			unique_id="temp_1",
			device_info={
				"identifiers": set(),
			},
		).validate()

def test_device_info_identifier_wrong_tuple_length():
	with pytest.raises(EntityError):
		Entity(
			domain=HADomain.SENSOR,
			name="Temp",
			unique_id="temp_1",
			device_info={
				"identifiers": {
					("only_one_value",)
				},
			},
		).validate()

def test_device_info_identifier_empty_key():
	with pytest.raises(EntityError):
		Entity(
			domain=HADomain.SENSOR,
			name="Temp",
			unique_id="temp_1",
			device_info={
				"identifiers": {
					("", "device_1")
				},
			},
		).validate()

def test_device_info_identifier_empty_value():
	with pytest.raises(EntityError):
		Entity(
			domain=HADomain.SENSOR,
			name="Temp",
			unique_id="temp_1",
			device_info={
				"identifiers": {
					("ha_mqtt_sdk", "")
				},
			},
		).validate()

def test_valid_connections():
	Entity(
		domain=HADomain.SENSOR,
		name="Temp",
		unique_id="temp_1",
		device_info={
			"connections": [
				("mac", "AA:BB:CC:DD:EE:FF")
			],
		},
	).validate()

def test_empty_connections():
	with pytest.raises(EntityError):
		Entity(
			domain=HADomain.SENSOR,
			name="Temp",
			unique_id="temp_1",
			device_info={
				"connections": set(),
			},
		).validate()

def test_valid_via_device():
	Entity(
		domain=HADomain.SENSOR,
		name="Temp",
		unique_id="temp_1",
		device_info={
			"identifiers": [
				("ha_mqtt_sdk", "device_1")
			],
			"via_device": (
				"ha_mqtt_sdk",
				"gateway_1",
			),
		},
	).validate()

def test_invalid_via_device_length():
	with pytest.raises(EntityError):
		Entity(
			domain=HADomain.SENSOR,
			name="Temp",
			unique_id="temp_1",
			device_info={
				"identifiers": {
					("ha_mqtt_sdk", "device_1")
				},
				"via_device": (
					"gateway_1",
				)
			},
		).validate()

def test_device_info_manufacturer_must_be_string():
	with pytest.raises(EntityError):
		Entity(
			domain=HADomain.SENSOR,
			name="Temp",
			unique_id="temp_1",
			device_info={
				"identifiers": {
					("ha_mqtt_sdk", "device_1")
				},
				"manufacturer": 123,
			},
		).validate()


