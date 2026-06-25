"""
Home Assistant MQTT SDK - Core Package

This is the main package initializer for the SDK.
It exposes the top-level API for external SDK users.

Responsibilities:
- Ensure logger is initialized
- Import key modules for convenient external use
- Maintain SDK-level metadata

Exports:
- HASDK
- Entity
- HADomain
- DeviceInfo
- create_device_info
- create_entity

Usage:
    from ha_mqtt_sdk import HASDK
    from ha_mqtt_sdk import AsyncHASDK

    from ha_mqtt_sdk import Entity
    from ha_mqtt_sdk import create_entity

    from ha_mqtt_sdk import HADomain

    from ha_mqtt_sdk import PahoMQTTClient
    from ha_mqtt_sdk import AsyncMQTTClient

    from ha_mqtt_sdk import DeviceInfo
    from ha_mqtt_sdk import create_device_info

    from ha_mqtt_sdk import get_logger
"""

from importlib.metadata import version

from .config.domains import HADomain
from .core.async_sdk import AsyncHASDK
from .core.device_factory import create_device_info
from .core.entity_factory import create_entity
from .core.sdk import HASDK
from .models.device_info import DeviceInfo
from .models.entity import Entity
from .mqtt.async_client import AsyncMQTTClient
from .mqtt.paho_client import PahoMQTTClient
from .utils.logger import get_logger

# Version
__version__ = version("ha_mqtt_sdk")

# Central SDK logger
LOGGER = get_logger(__name__)

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
    # MQTT Clients - needed for dependeny injection
    "PahoMQTTClient",
    "AsyncMQTTClient",
]
