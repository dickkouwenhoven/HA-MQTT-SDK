"""
async_plugin_manager.py

Registry and lifecycle manager for asynchronous AsyncIntegrationPlugins.

Responsibilities:
- Register and retrieve plugins by name
- Drive the async plugin lifecycle: setup → start → stop

Used by:
- ha_mqtt_sdk/core/async_sdk.py (AsyncHASDK.use_plugin / AsyncHASDK.run)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .async_plugin_interface import AsyncIntegrationPlugin
from .utils.logger import get_logger

if TYPE_CHECKING:
    from .async_sdk import AsyncHASDK

_logger = get_logger(__name__)


class AsyncPluginManager:
    """
    Manages the lifecycle of asynchronous AsyncIntegrationPlugins.

    Typically not used directly — accessed via AsyncHASDK.use_plugin()
    and AsyncHASDK.run().
    """

    def __init__(self, sdk: AsyncHASDK) -> None:
        self._sdk = sdk
        self._plugins: dict[str, AsyncIntegrationPlugin] = {}

    # -------------------------
    # Registration
    # -------------------------

    def register(self, name: str, plugin: AsyncIntegrationPlugin) -> None:
        """
        Register a plugin by name.

        Args:
            name:   Unique identifier for this integration (e.g. "dirigera", "hue")
            plugin: AsyncIntegrationPlugin instance

        Raises:
            ValueError: If a plugin with this name is already registered
            TypeError:  If plugin is not an AsyncIntegrationPlugin
        """
        if name in self._plugins:
            raise ValueError(f"Plugin '{name}' is already registered")

        if not isinstance(plugin, AsyncIntegrationPlugin):
            raise TypeError(f"Plugin must be an AsyncIntegrationPlugin, got {type(plugin)}")

        self._plugins[name] = plugin
        _logger.debug("Plugin registered: %s", name)

    def get(self, name: str) -> AsyncIntegrationPlugin:
        """
        Retrieve a registered plugin by name.

        Args:
            name: Plugin identifier

        Raises:
            KeyError: If no plugin is registered with this name
        """
        if name not in self._plugins:
            raise KeyError(f"No plugin registered with name '{name}'")

        return self._plugins[name]

    # -------------------------
    # Lifecycle
    # -------------------------

    async def setup_all(self) -> None:
        """
        Call setup(sdk) on every registered plugin.

        Plugins are set up in registration order.
        """
        for name, plugin in self._plugins.items():
            _logger.info("Setting up plugin: %s", name)
            await plugin.setup(self._sdk)
            _logger.info("Plugin setup complete: %s", name)

    async def start_all(self) -> None:
        """
        Call start() on every registered plugin.

        Called after setup_all() completes.
        """
        for name, plugin in self._plugins.items():
            _logger.info("Starting plugin: %s", name)
            await plugin.start()
            _logger.info("Plugin started: %s", name)

    async def stop_all(self) -> None:
        """
        Call stop() on every registered plugin.

        Errors from individual plugins are caught and logged so that
        all plugins get a chance to stop cleanly.
        """
        for name, plugin in self._plugins.items():
            _logger.info("Stopping plugin: %s", name)
            try:
                await plugin.stop()
                _logger.info("Plugin stopped: %s", name)
            except Exception as e:
                _logger.error("Error stopping plugin '%s': %s", name, e)
