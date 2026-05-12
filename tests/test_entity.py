import pytest
import ha-mqtt-sdk.models.entity import Entity
import ha-mqtt-sdk.config.domains import HADomain

def test_valid_entity():
	entity = Entity(
		domain = HADomain.SENSOR,
		name = "Temp",
		unique_id = "temp_1",
		state_topic = "test/topic",
	)
	entity.validate()

def test_missing_name():
	with pytest.raises(ValueError):
		Entity(
			domain = HADomain.SENSOR,
			name = "",
			unique_id = "id",
		).validate()

def test_invalid_domain():
	with pytest.raises(ValueError):
		Entity(
			domain = "invalid",
			name = "Test",
			unique_id = "id",
		).validate()


