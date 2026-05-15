import pytest
from ha_mqtt_sdk.config.mqtt import MQTTSettings
from unittest.mock import MagicMock, AsyncMock

class MockMQTTClient:
	def __init__(self):
		self.published = []
		self.subscribed = []
		self.callback = None

	def publish(
		self,
		topic,
		payload,
		retain = False,
	):
		self.published.append((topic, payload, retain))

	def subscribe(
		self,
		topic,
	):
		self.subscribed.append(topic)

	def set_message_callback(
		self,
		callback,
	):
		self.callback = callback

	def set_last_will(
		self,
		topic,
		payload="offline",
	):
		self.last_will = (topic, payload)

	def simulate_message(self, topic, payload):
		if self.callback:
			self.callback(
				topic,
				payload
			)

@pytest.fixture
def mqtt_client():
	return MockMQTTClient()

@pytest.fixture
def mqtt_settings():
	return MQTTSettings(
		discovery_prefix="homeassistant"
	)
