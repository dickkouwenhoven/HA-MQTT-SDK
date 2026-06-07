"""
Basic example showing how to use the HASDK.
"""

from ha_mqtt_sdk import EntityManager, HADomain, MQTTSettings, PahoMQTTClient


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
	mqtt_config = MQTTSettings(
		host="localhost",
		port=1883,
	)
	
	client = PahoMQTTClient(
		config = mqtt_config
	)

	manager = HASDK(
		mqtt_client=client,
	)

	# Create entity
	light = Entity(
		domain=HADomain.LIGHT,
		name="Demo Lamp",
		unique_id="demo_lamp"
	)

	# Register in HA
	manager.register(light)

	# Set availability
	manager.update_availability(light, True)

	# Send state
	manager.update_state(light, "ON")


if __name__ == "__main__":
	main()
