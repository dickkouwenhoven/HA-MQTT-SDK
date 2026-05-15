from ha_mqtt_sdk.core.entity_manager import EntityManager
from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.builders.topic_manager import build_state_topic
from ha_mqtt_sdk.builders.topic_manager import build_command_topic

def test_create_entity(mqtt_client_sync):
	manager = EntityManager(
		mqtt_client_sync,
		MQTTSettings(
			discovery_prefix="homeassistant"
		)
	)

	entity = manager.create_entity(
		domain = HADomain.SENSOR,
		name = "Temp",
		unique_id = "temp_1",
	)

	assert entity.unique_id == "temp_1"
	assert entity.domain == HADomain.SENSOR


def test_register_entity(mqtt_client_sync):
	manager = EntityManager(
		mqtt_client_sync,
		MQTTSettings(
			discovery_prefix="homeassistant"
		)
	)

	entity = manager.create_entity(
		domain = HADomain.SWITCH,
		name = "Switch",
		unique_id = "switch_1",
	)

	manager.register(entity)

	assert len(mqtt_client.published) > 0


def test_command_subscription(mqtt_client_sync):
	manager = EntityManager(
		mqtt_client_sync,
		MQTTSettings(
			discovery_prefix="homeassistant"
		)
	)

	entity = manager.create_entity(
		domain = HADomain.SWITCH,
		name = "Switch",
		unique_id = "switch_1",
	)

	manager.register(entity)

	expected_topic = build_command_topic(
		entity.domain,
		entity.unique_id,
		"homeassistant",
	)

	assert expected_topic in mqtt_client.subscribed


def test_update_state(mqtt_client_sync):
	manager = EntityManager(
		mqtt_client_sync,
		MQTTSettings(
			discovery_prefix="homeassistant"
		)
	)

	entity = manager.create_entity(
		domain = HADomain.SENSOR,
		name = "Temp",
		unique_id = "temp_1",
	)

	manager.update_state(entity, 25)

	assert ("homeassistant/sensor/temp_1/state", 25, False) in mqtt_client_sync.published.published


def test_update_availability(mqtt_client_sync):
	manager = EntityManager(
		mqtt_client_sync,
		MQTTSettings(
			discovery_prefix="homeassistant"
		)
	)

	entity = manager.create_entity(
		domain = HADomain.SENSOR,
		name = "Temp",
		unique_id = "temp_1",
	)

	manager.update_availability(entity, True)

	topic, payload, retain = mqtt_client.published[-1]

	assert payload == "online"
	assert retain is True


def test_command_callback_execution(mqtt_client_sync):
	manager = EntityManager(
		mqtt_client_sync,
		MQTTSettings(
			discovery_prefix="homeassistant"
		)
	)

	entity = manager.create_entity(
		domain = HADomain.SWITCH,
		name = "Switch",
		unique_id = "switch_1",
	)

	called = {"value": False}

	def callback(topic, payload):
		called["value"] = True

	manager.register(
		entity,
		command_callback=callback
	)

	# Simulate MQTT message
	expected_topic = build_command_topic(
		entity.domain,
		entity.unique_id,
		"homeassistant",
	)

	mqtt_client_sync.simulate_message(expected_topic, "ON")

	assert called["value"] is True
	
