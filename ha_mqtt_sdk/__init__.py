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

Usage:
    from ha_mqtt_sdk import HASDK
	
	from ha_mqtt_sdk import EntityManager
	from ha_mqtt_sdk import AsyncEntityManager
	
	from ha_mqtt_sdk import Entity
	
	from ha_mqtt_sdk import HADomain
	from ha_mqtt_sdk import MQTTSettings
	
	from ha_mqtt_sdk import PahoMQTTClient
	from ha_mqtt_sdk import AsyncMQTTClient
	
	from ha_mqtt_sdk import get_logger	
"""

from .utils.logger import get_logger

# Central SDK logger
LOGGER = get_logger(__name__)

# Top-level imports for SDK users
from .core.sdk import HASDK

from .core.entity_manager import EntityManager
from .core.async_entity_manager import AsyncEntityManager

from .models.entity import Entity

from .config.domains import HADomain
from .config.mqtt import MQTTSettings

from .mqtt.paho_client import PahoMQTTClient
from .mqtt.async_client import AsyncMQTTClient

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
	"get_logger"
]
