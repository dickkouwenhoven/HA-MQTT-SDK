"""
Home Assistant MQTT SDK - Core Package

This is the main package initializer for the SDK. 
It exposes the top-level API for external SDK users.

Responsibilities:
- Ensure logger is initialized
- Import key modules for convenient external use
- Maintain SDK-level metadata

Usage:
    from sdk import mqtt_client, models, config
"""

from .utils.logger import get_logger

# Central SDK logger
LOGGER = get_logger(__name__)

# Top-level imports for SDK users
from .core.sdk import HASDK
from .models.entity import Entity
from .models.device import DeviceInfo
from .config.domains import HADomain

__all__ = [
	"HASDK",
	"Entity",
	"DeviceInfo",
	"HADomain",
]

