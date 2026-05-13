"""
Base MQTT client interface.

This defines the contract for all MQTT client implementations.
Both sync and async clients must adhere to this interface.

Used by:
- ha_mqtt_sdk/core/sdk.py (HASDK)
"""

from abc import ABC, abstractmethod
from typing import Callable, Any


class BaseMQTTClient(ABC):
	"""
	Abstract base MQTT client.
	"""

	@abstractmethod
	def connect(self) -> None:
		"""Establish connection to the MQTT broker."""

	@abstractmethod
	def disconnect(self) -> None:
		"""Disconnect from the MQTT broker."""

	@abstractmethod
	def publish(self, topic: str, payload: Any, retain: bool = False) -> None:
		"""Publish a message to a topic. """

	@abstractmethod
	def subscribe(self, topic: str, callback: Callable[[str, Any], None]) -> None:
		"""Subscribe to a topic and register a message callback."""

	@abstractmethod
	def set_message_callback(self, callback: Callable[[str, Any], None]) -> None:
		"""Register a global message handler."""
