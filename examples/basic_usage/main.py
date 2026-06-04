"""
Basic example showing how to use the HASDK.
"""

from ha_mqtt_sdk.core.entity_manager import EntityManager
from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.mqtt import PahoMQTTClient


class SimpleMQTT:
	def __init__(self):
		self.callback = None
	
	@staticmethod	
	def publish(self, topic, payload, retain=False):
		print(f"[MQTT PUBLISH] {topic} -> {payload} -> {retain}")

	@staticmethod
	def subscribe(self, topic):
		print(f"[MQTT SUBSCRIBE] {topic}")

	def set_message_callback(self, cb):
		self.callback = cb


def main():
	mqtt = PahoMQTTClient(
		config = mqtt_config
	)

	manager = EntityManager(
		mqtt,
		MQTTSettings(
			discovery_prefix="homeassistant"
		)
	)

	# Create entity
	entity = manager.create_entity(
		domain=HADomain.LIGHT,
		name="Demo Lamp",
		unique_id="demo_lamp"
	)

	# Register in HA
	manager.register(entity)

	# Set availability
	manager.update_availability(entity, True)

	# Send state
	manager.update_state(entity, "ON")


if __name__ == "__main__":
	main()
