"""
Configuration layer

Contains:
- Domain definitions
- Schema definitions
- MQTT settings
"""

from .domains import HADomain
from .schemas import ComponentSchema
from .device_fields import ALLOWED_FIELDS_PER_DOMAIN
from .mqtt import MQTTSettings

__all__ = [
	"HADomain",
	"ComponentSchema",
	"ALLOWED_FIELDS_PER_DOMAIN",
	"MQTTSettings"
]

