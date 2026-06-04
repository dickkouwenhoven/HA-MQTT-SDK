"""
Test script for Home Assistant MQTT SDK

Verifies:
- Entity creation,
- Validation
- Discovery payload generation
- Discovery topic generation
- MQTT publish calls
- Full entity manager flow
"""

import unittest
from unittest.mock import MagicMock

from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.config.mqtt import MQTTSettings

from ha_mqtt_sdk.models.entity import Entity
from ha_mqtt_sdk.core.entity_manager import EntityManager

from ha_mqtt_sdk.builders.discovery_payload import build_discovery_payload
from ha_mqtt_sdk.builders.topic_manager import build_discovery_topic

from ha_mqtt_sdk.mqtt.paho_client import PahoMQTTClient
from ha_mqtt_sdk.exceptions import EntityError
from ha_mqtt_sdk.utils.logger import get_logger

LOGGER = get_logger("test_sdk")

class TestHomeAssistantSDK(unittest.TestCase):

	def setUp(self):
		"""
		Create mocked MQTT client.
		"""
		config = MQTTSettings(
			host="localhost",
			port=1883,
		)
			
		self.mqtt_client = PahoMQTTClient(config)

		# Mock underlying paho publish
		self.mqtt_client._client.publish = MagicMock()
		self.mqtt_client._client.subscribe = MagicMock()
		
		LOGGER.info("Setup complete")

	# ------------------------------------
	# Entity tests
	# ------------------------------------
	def test_entity_creation_valid(self):
		
		entity = Entity(
    		domain=HADomain.SENSOR,
    		name="Temperature Sensor",
    		unique_id="temp_sensor_1",
		)

		entity.validate()
		
		self.assertEqual(entity.name, "Temperature Sensor")
		self.assertEqual(entity.unique_id, "temp_sensor_1")

	def test_entity_creation_invalid_name(self):
		
		with self.assertRaises(EntityError):

			entity = Entity(
				domain=HADomain.SENSOR,
				name="",
				unique_id="temp_sensor_1",
			)
			entity.validate()
	
	def test_discovery_payload(self):

		entity = Entity(
			domain=HADomain.LIGHT,
			name="Living Room Light",
			unique_id="livingroom_light_1",			
		)
		
		payload = build_discovery_payload(
			entity, 
			"homeassistant",
		)
		
		self.assertEqual(payload["name"], "Living Room Light")
		self.assertIn("command_topic", payload)

	# -----------------------------------
	# MQTT publish
	# -----------------------------------
	
	def test_mqtt_publish(self):
	
		topic = "homeassistant/test_sensor/config"
		
		payload = {
			"name": "Test Sensor", 
			"unique_id": "test_sensor"
		}
		
		self.mqtt_client.publish(topic, payload)
		
		self.mqtt_client._client.publish.assert_called_once()
		
		args, kwargs = self.mqtt_client._client.publish.call_args
		
		self.assertEqual(args[0], topic)
		self.assertIn("Test Sensor", args[1])

	# -----------------------------------
	# Logger
	# -----------------------------------
	
	def test_logger_dual_mode(self):
		# Should use existing logger
		custom_logger = get_logger("custom_test_logger")
		self.assertEqual(
			custom_logger.name,
			"custom_test_logger"
		)

	# -----------------------------------
	# Full flow
	# -----------------------------------

	def test_full_flow(self):
	
		manager = EntityManager(
			self.mqtt_client,
			MQTTSettings(
				discovery_prefix = "homeassistant"
			)
		)

		# Create entity
		entity = manager.create_entity(
			domain = HADomain.LIGHT,
			name = "Lamp",
			unique_id = "lamp_1",
		)

		# Register entity
		manager.register(entity)

		# Update state
		manager.update_state(entity, "ON")

		# Update availability
		manager.update_availability(entity, True)

		# Ensure MQTT publish happened
		self.assertTrue(
			self.mqtt_client._client.publish.called
		)	


	def test_full_flow_sensor(self):
	
		manager = EntityManager(
			self.mqtt_client,
			MQTTSettings(
				discovery_prefix="homeassistant"
			)
		)
	
		entity = manager.create_entity(
			domain=HADomain.SENSOR,
			name="Temperature",
			unique_id="temp_1",
		)
	
		manager.register(entity)

    	# Should not subscribe to command topics
		self.mqtt_client._client.subscribe.assert_not_called()		

if __name__ == "__main__":
	unittest.main()
