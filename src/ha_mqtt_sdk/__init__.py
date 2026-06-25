"""
Home Assistant MQTT SDK

Public API - everything a user needs is importable from this package:

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
from .exceptions import (
    SDKError,
    ValidationError,
    BuilderError,
    EntityError,
    SchemaError,
    MQTTError,
    MQTTConnectionError,
    MQTTPublishError,
    PluginError,
    ConfigurationError,
)
from .models.device_info import DeviceInfo
from .models.entity import Entity
from .mqtt.async_client import AsyncMQTTClient
from .mqtt.paho_client import PahoMQTTClient

# Version
__version__ = version("ha_mqtt_sdk")

__all__ = [
    # Sync entry point
    "HASDK",
    # Async entry point
    "AsyncHASDK",
    # Configuration
    "MQTTSettings",
    # Domain types
    "HADomain",
    "Entity",
    "create_entity",
    "DeviceInfo",
    "create_device_info",
    # MQTT Clients - needed for dependeny injection
    "PahoMQTTClient",
    "AsyncMQTTClient",
    # Plugin base classes - needed to build integrations
    "IntegrationPlugin",
    "AsyncIntegrationPlugin",
    # Exceptions
    "SDKError",
    "ValidationError",
    "BuilderError",
    "EntityError",
    "SchemaError",
    "MQTTError",
    "MQTTConnectionError",
    "MQTTPublishError",
    "PluginError",
    "ConfigurationError",
]
