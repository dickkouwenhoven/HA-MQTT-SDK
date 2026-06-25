"""
Home Assistant MQTT SDK

This is the main package initializer for the SDK.
It exposes the top-level API for external SDK users.

Responsibilities:
- Ensure logger is initialized
- Import key modules for convenient external use
- Maintain SDK-level metadata

Exports:
- HASDK
- AsyncHASDK
- Entity
- HADomain
- MQTTSettings
- DeviceInfo
- create_device_info
- create_entity
- AsyncMQTTClient
- PahoMQTTClient

Usage:
    from ha_mqtt_sdk import HASDK, AsyncHASDK
    from ha_mqtt_sdk import Entity, create_entity
    from ha_mqtt_sdk import HADomain
    from ha_mqtt_sdk import MQTTSettings
    from ha_mqtt_sdk import PahoMQTTClient, AsyncMQTTClient
    from ha_mqtt_sdk import DeviceInfo, create_device_info
    from ha_mqtt_sdk import IntegrationPlugin, AsyncIntegrationPlugin
"""

from importlib.metadata import version

from .config.domains import HADomain
from .config.mqtt import MQTTSettings
from .core.async_plugin_interface import AsyncIntegrationPlugin
from .core.async_sdk import AsyncHASDK
from .core.device_factory import create_device_info
from .core.entity_factory import create_entity
from .core.plugin_interface import IntegrationPlugin
from .core.sdk import HASDK
from .models.device_info import DeviceInfo
from .models.entity import Entity
from .mqtt.async_client import AsyncMQTTClient
from .mqtt.paho_client import PahoMQTTClient

# Version
__version__ = version("ha_mqtt_sdk")

__all__ = [
    # Primary entry point
    "HASDK",
    # Async entry point
    "AsyncHASDK",
    # Domain types users must construct
    "Entity",
    "create_entity",
    "HADomain",
    "DeviceInfo",
    "create_device_info",
    "MQTTSettings",
    # MQTT Clients - needed for dependeny injection
    "PahoMQTTClient",
    "AsyncMQTTClient",
    "IntegrationPlugin",
    "AsyncIntegrationPlugin",
]
