"""
MQTT layer.

Provides:
- Base client interface
- Sync (Paho) implementation
- Async implementation
"""

from .async_client import AsyncMQTTClient
from .base import BaseMQTTClient

# Optional Paho import
try:
	from .paho_client import PahoMQTTClient
except ModuleNotFoundError: # pragma: no cover
	PahoMQTTClient = None

__all__ = [
	"BaseMQTTClient",
	"PahoMQTTClient",
	"AsyncMQTTClient",
]
