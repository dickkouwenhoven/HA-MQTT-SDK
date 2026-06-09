"""
Base MQTT client interface.

This defines the contract for all MQTT client implementations.
Both sync and async clients must adhere to this interface.

Used by:
- ha_mqtt_sdk/core/sdk.py (HASDK)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

MessageCallback = Callable[[str, str], None]


class BaseMQTTClient(ABC):
    """
    Base MQTT transport interface.

    All MQTT transport implementations must inherit from this class.
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the MQTT broker."""

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""

    @abstractmethod
    def publish(self, topic: str, payload: str, retain: bool = False) -> None:
        """Publish a message to a topic."""

    @abstractmethod
    def subscribe(self, topic: str, callback: MessageCallback) -> None:
        """Subscribe to a topic and register a message callback."""

    @abstractmethod
    def set_message_callback(self, callback: MessageCallback) -> None:
        """Register a global message handler."""
