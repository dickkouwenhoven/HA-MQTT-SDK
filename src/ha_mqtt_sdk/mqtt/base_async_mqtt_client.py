"""
Async MQTT client interface.

This defines the contract for all async MQTT client implementations.
Async clients must inherit from this class and implement all abstract methods.

Used by:
- ha_mqtt_sdk/core/async_sdk.py (AsyncHASDK)
- ha_mqtt_sdk/core/async_entity_manager.py (AsyncEntityManager)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

MessageCallback = Callable[[str, str], Awaitable[None]]

type PublishPayload = str | dict[str, Any] | int | float


class BaseAsyncMQTTClient(ABC):
    """
    Base MQTT transport interface.

    All MQTT transport implementations must inherit from this class.
    """

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the MQTT broker."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""

    @abstractmethod
    async def publish(self, topic: str, payload: PublishPayload, retain: bool = False) -> None:
        """Publish a message to a topic."""

    @abstractmethod
    async def subscribe(self, topic: str) -> None:
        """Subscribe to a topic."""

    @abstractmethod
    def set_message_callback(self, callback: MessageCallback) -> None:
        """Register a global message handler."""
