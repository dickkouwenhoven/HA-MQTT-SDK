"""
Core orchestration layer.

Contains the SDK entry points, entity managers, entity factory,
and plugin system.

Most users should import from the top-level package instead:

    from ha_mqtt_sdk import HASDK, AsyncHASDK

Import directly from this module only when you need lower-level access,
for example when subclassing a manager or working with the plugin system.
"""

from .async_entity_manager import AsyncEntityManager
from .async_plugin_interface import AsyncIntegrationPlugin
from .async_plugin_manager import AsyncPluginManager
from .async_sdk import AsyncHASDK
from .entity_factory import EntityRegistration, build_registration, create_entity
from .entity_manager import EntityManager
from .plugin_interface import IntegrationPlugin
from .plugin_manager import PluginManager
from .sdk import HASDK

__all__ = [
    # Sync path
    "HASDK",
    "EntityManager",
    "PluginManager",
    "IntegrationPlugin",
    # Async path
    "AsyncHASDK",
    "AsyncEntityManager",
    "AsyncPluginManager",
    "AsyncIntegrationPlugin",
    # Shared factory
    "create_entity",
    "build_registration",
    "EntityRegistration",
]
