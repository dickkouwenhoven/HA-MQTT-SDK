"""
MQTT related SDK configureren.

Single source of truth for MQTT topic structure.
"""

from ..exceptions import ConfigurationError

class MQTTSettings:
	def __init__(
		self,
		discovery_prefix: str | None = None,
	):
		self.discovery_prefix = (
			discovery_prefix
			if discovery_prefix is not None
			else os.getenv("MQTT_DISCOVERY_PREFIX", "homeassistant")
		)
		if not isinstance(discovery_prefix, str) or not discovery_prefix.strip():
			raise ConfigurationError("discovery_prefix must be a non-empty string")

		self.discovery_prefix = discovery_prefix
