"""
MQTT configuration validation.

Used by:
- paho_client.py
- asyncio_client.py
"""

from typing import Optional
from ..exceptions import MQTTError, ConfigurationError

class MQTTConfig:
	def __init__(
		self,
		host: str,
		port: int = 1883,
		username: Optional[str] = None,
		password: Optional[str] = None,
		client_id: Optional[str] = None,
		keepalive: int = 60,
		tls: bool = False,
		reconnect: bool = True,
		reconnect_delay_min: float = 1.0,
		reconnect_delay_max: float = 60.0,
	):
		self._validate(host, port, keepalive)

		self.host = host
		self.port = port
		self.username = username
		self.password = password
		self.client_id = client_id
		self.keepalive = keepalive
		self.tls = tls
		self.reconnect = reconnect
		self.reconnect_delay_min = reconnect_delay_min
		self.reconnect_delay_max = reconnect_delay_max

	def _validate(self, host: str, port: int, keepalive: int) -> None:
		if not host:
			raise MQTTError("MQTT host must not be empty")

		if not isinstance(port, int) or port <= 0:
			raise MQTTError("MQTT port must be a positive integer")

		if keepalive <= 0:
			raise MQTTError("Keepalive must be > 0")
