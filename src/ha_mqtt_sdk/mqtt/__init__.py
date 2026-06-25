"""
MQTT layer.

Provides the MQTT client interfaces and implementations for both
sync and async paths.

Most users should import clients from the top-level package:

    from ha_mqtt_sdk import PahoMQTTClient, AsyncMQTTClient

Import directly from this module when you need the base classes
for dependency injection or writing a custom MQTT transport:

    from ha_mqtt_sdk.mqtt import BaseMQTTClient, BaseAsyncMQTTClient
"""

from .async_client import AsyncMQTTClient
from .base import BaseMQTTClient
from .base_async_mqtt_client import BaseAsyncMQTTClient
from .paho_client import PahoMQTTClient

__all__ = [
    # Sync path
    "BaseMQTTClient",
    "PahoMQTTClient",
    # Async path
    "BaseAsyncMQTTClient",
    "AsyncMQTTClient",
]
