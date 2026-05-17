"""
MQTT configuration validation.

Used by:
- paho_client.py
- asyncio_client.py
"""

import os
from typing import Optional
from ..exceptions import MQTTError, ConfigurationError

class MQTTConfig:
	def __init__(
		self,
		host: str | None = None,
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

		self.host = (
			host
			or os.getenv(
				"MQTT_HOST",
				"mqtt"
			)
		)
		self.port = (
			port
			or os.getenv(
				"MQTT_PORT",
				"1883"
			)
		)
		self.username = (
			username
			or os.getenv(
				"MQTT_USER",
				"hauser"
			)
		)
		self.password = (
			password
			or os.getenv(
				"MQTT_PASSWORD",
				""
			)
		)
		self.client_id = client_id
		self.keepalive = (
			keepalive
			or os.getenv(
				"MQTT_KEEPALIVE",
				60
			)
		)
		self.tls = tls
		self.reconnect = (
			reconnect
			or os.getenv(
				"RECONNECT",
				True
			)
		)
		self.reconnect_delay_min = (
			reconnect_delay_min
			or os.getenv(
				"RECONNECT_DELAY_MIN",
				1.0
			)
		)
		self.reconnect_delay_max = (
			reconnect_delay_max
			or os.getenv(
				"RECONNECT_DELAY_MAX",
				60.0
			)
		)
		

	def _validate(self, host: str, port: int, keepalive: int) -> None:
		if not host:
			raise MQTTError("MQTT host must not be empty")

		if not isinstance(port, int) or port <= 0:
			raise MQTTError("MQTT port must be a positive integer")

		if keepalive <= 0:
			raise MQTTError("Keepalive must be > 0")
