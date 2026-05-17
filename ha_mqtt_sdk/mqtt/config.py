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
		port: int | None = None,
		username: Optional[str] = None,
		password: Optional[str] = None,
		client_id: Optional[str] = None,
		keepalive: int | None = None,
		tls: bool = False,
		reconnect: bool | None = None,
		reconnect_delay_min: float | None = None,
		reconnect_delay_max: float | None = None,
	):
		self.host = (
			host
			if host is not None
			else os.getenv("MQTT_HOST", "mqtt")
		)
		
		self.port = (
			port
			if port is not None
			else int(os.getenv("MQTT_PORT",	1883))
		)
		
		self.username = (
			username
			if username is not None
			else os.getenv("MQTT_USER", "hauser")
		)
		
		self.password = (
			password
			if password is not None
			else os.getenv("MQTT_PASSWORD", "")
		)
		
		self.client_id = client_id
		
		self.keepalive = (
			keepalive
			if keepalive is not None
			else int(os.getenv("MQTT_KEEPALIVE", 60))
		)
		
		self.tls = tls
		
		self.reconnect = (
			reconnect
			if reconnect is not None
			else os.getenv("RECONNECT", "True").lower() == "true"
		)
		
		self.reconnect_delay_min = (
			reconnect_delay_min
			if reconnect_delay_min is not None
			else float(os.getenv("RECONNECT_DELAY_MIN", 1.0))
		)
		
		self.reconnect_delay_max = (
			reconnect_delay_max
			if reconnect_delay_max is not None
			else float(os.getenv("RECONNECT_DELAY_MAX", 60.0))
		)

		self._validate()
		

	def _validate(self) -> None:
		
		if not self.host:
			raise MQTTError("MQTT host must not be empty")

		if not isinstance(self.port, int) or self.port <= 0:
			raise MQTTError("MQTT port must be a positive integer")

		if self.keepalive <= 0:
			raise MQTTError("Keepalive must be > 0")

		if self.reconnect_delay_min <= 0:
			raise MQTTError("Reconnect delay min must be > 0")

		if self.reconnect_delay_max < self.reconnect_delay_min:
			raise MQTTError("Reconnect delay max must be >= reconnect delay min")
