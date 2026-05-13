"""
MQTT related SDK configureren.

Single source of truth for MQTT topic structure.
"""

..exceptions import ConfigurationError

class MQTTSettings:
	def __init__(
		self,
		discovery_prefix = "homeassistant",
	):
		if not isinstance(discovery_prefix, str) or not discovery_prefix.strip():
			raise ConfigurationError("discovery_prefix must be a non-empty string")

		self.discovery_prefix = discovery_prefix

