"""
Test script for Home Assistant MQTT SDK

- Verifies entity creation, discovery payloads, topic generation
- Mocked MQTT publish to ensure safe testing without broker
- Logger output verification
"""

import unittest
from unittest.mock import patch, MagicMock
from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.core.entity_manager import EntityManager
from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.entity import Entity
from ha_mqtt_sdk.mqtt.topic_manager import build_discovery_topic
from ha_mqtt_sdk.mqtt.discovery_payload import build_discovery_payload
from ha_mqtt_sdk.mqtt.mqtt_client import MQTTClient
from ha_mqtt_sdk.utils.logger import get_logger

LOGGER = get_logger("test_sdk")

class TestHomeAssistantSDK(unittest.TestCase):

	def setUp(self):
		# Mock MQTT broker
		self.mqtt_client = MQTTClient(host="localhost")
		self.mqtt_client.client.publish = MagicMock()
		LOGGER.info("Setup complete")

	def test_entity_creation_valid(self):
		entity = Entity(
    		domain=HADomain.SENSOR,
    		name="Temperature Sensor",
    		unique_id="temp_1",
    		state_topic="sensor/temp",
		)
		
		self.assertIn("unique_id", entity)
		self.assertEqual(entity.name, "Temperature Sensor")
		self.assertEqual(entity.state_topic, "sensor/temp")

	def test_entity_creation_missing_required(self):
		with self.assertRaises(ValueError):
			# Missing required field for SENSOR
			entity = Entity(
				domain=HADomain.SENSOR,
				name="",
				unique_id="temp_1",
			)
			entity.validate()
	
	def test_discovery_payload(self):
		payload = build_discovery_payload(HADomain.LIGHT, "Living Room Light",
			command_topic="home/livingroom/light/set")
		self.assertEqual(payload["name"], "Living Room Light")
		self.assertIn("command_topic", payload)

	def test_build_discovery_topic(self):
		topic = build_discovery_topic(HADomain.SENSOR, "unique_sensor_id")
		self.assertTrue(topic.startswith("homeassistant/sensor/unique_sensor_id"))

	def test_mqtt_publish(self):
		topic = "homeassistant/test_sensor/config"
		payload = {"name": "Test Sensor", "unique_id": "test_sensor"}
		self.mqtt_client.publish(topic, payload)
		self.mqtt_client.client.publish.assert_called_once()
		args, kwargs = self.mqtt_client.client.publish.call_args
		self.assertEqual(args[0], topic)
		self.assertIn("Test Sensor", args[1])

	def test_logger_dual_mode(self):
		# Should use existing logger
		custom_logger = get_logger("custom_test_logger")
		self.assertIsNotNone(custom_logger)

def test_full_flow(mqtt_client):
	manager = EntityManager(
		mqtt_client,
		MQTTSettings(
			discovery_prefix = "homeassistant"
		)
	)

	# Create
	entity = manager.create_entity(
		domain = HADomain.LIGHT,
		name = "Lamp",
		unique_id = "lamp_1",
	)

	# Register
	manager.register(entity)

	# State update
	manager.update_state(entity, "ON")

	# Availability
	manager.update_availability(entity, True)

	assert len(mqtt_client.published) >= 3

if __name__ == "__main__":
	unittest.main()
