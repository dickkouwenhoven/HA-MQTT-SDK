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
	from ha_mqtt_sdk import Entity
	from ha_mqtt_sdk import HADomain
	from ha_mqtt_sdk import MQTTSettings
"""

from .utils.logger import get_logger

# Central SDK logger
LOGGER = get_logger(__name__)

# Top-level imports for SDK users
from .core.sdk import HASDK
from .models.entity import Entity
from .config.domains import HADomain
from .config.mqtt import MQTTSettings

__version__ = "1.0.0"

__all__ = [
	"HASDK",
	"Entity",
	"HADomain",
	"MQTTSettings",
]
