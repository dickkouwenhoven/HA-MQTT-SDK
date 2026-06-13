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

Usage:
    from ha_mqtt_sdk import HASDK

        from ha_mqtt_sdk import EntityManager
        from ha_mqtt_sdk import AsyncEntityManager

        from ha_mqtt_sdk import Entity

        from ha_mqtt_sdk import HADomain
        from ha_mqtt_sdk import MQTTSettings

        from ha_mqtt_sdk import PahoMQTTClient
        from ha_mqtt_sdk import AsyncMQTTClient

        from ha_mqtt_sdk import DeviceInfo
        from ha_mqtt_sdk import create_device_info

        from ha_mqtt_sdk import get_logger
"""

from .config.domains import HADomain
from .config.mqtt import MQTTSettings
from .core.async_entity_manager import AsyncEntityManager
from .core.device_factory import create_device_info
from .core.entity_manager import EntityManager
from .core.sdk import HASDK
from .models.device_info import DeviceInfo
from .models.entity import Entity
from .mqtt.async_client import AsyncMQTTClient
from .mqtt.paho_client import PahoMQTTClient
from .utils.logger import get_logger

# Central SDK logger
LOGGER = get_logger(__name__)

__version__ = "1.0.0"

__all__ = [
    "HASDK",
    "EntityManager",
    "AsyncEntityManager",
    "Entity",
    "HADomain",
    "MQTTSettings",
    "PahoMQTTClient",
    "AsyncMQTTClient",
    "DeviceInfo",
    "create_device_info",
    "get_logger",
]
