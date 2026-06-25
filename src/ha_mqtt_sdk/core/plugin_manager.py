"""
plugin_manager.py

Registry and lifecycle manager for synchronous IntegrationPlugins.

Responsibilities:
- Register and retrieve plugins by name
- Drive the plugin lifecycle: setup → start → stop

Used by:
- ha_mqtt_sdk/core/sdk.py (HASDK.use_plugin / HASDK.run)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..exceptions import PluginError
from ..utils.logger import get_logger
from .plugin_interface import IntegrationPlugin

if TYPE_CHECKING:
    from .sdk import HASDK

_logger = get_logger(__name__)


class PluginManager:
    """
    Manages the lifecycle of synchronous IntegrationPlugins.

    Typically not used directly — accessed via HASDK.use_plugin()
    and HASDK.run().
    """

    def __init__(self, sdk: HASDK) -> None:
        self._sdk = sdk
        self._plugins: dict[str, IntegrationPlugin] = {}

    # -------------------------
    # Registration
    # -------------------------

    def register(self, name: str, plugin: IntegrationPlugin) -> None:
        """
        Register a plugin by name.

        Args:
            name:   Unique identifier for this integration (e.g. "hue", "zwave")
            plugin: IntegrationPlugin instance

        Raises:
            ValueError: If a plugin with this name is already registered
        """
        if name in self._plugins:
            raise PluginError(f"Plugin '{name}' is already registered")

        if not isinstance(plugin, IntegrationPlugin):
            raise PluginError(f"Plugin must be an IntegrationPlugin, got {type(plugin)}")

        self._plugins[name] = plugin
        _logger.debug("Plugin registered: %s", name)

    def get(self, name: str) -> IntegrationPlugin:
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

    def setup_all(self) -> None:
        """
        Call setup(sdk) on every registered plugin.

        Plugins are set up in registration order.
        """
        for name, plugin in self._plugins.items():
            _logger.info("Setting up plugin: %s", name)
            plugin.setup(self._sdk)
            _logger.info("Plugin setup complete: %s", name)

    def start_all(self) -> None:
        """
        Call start() on every registered plugin.

        Called after setup_all() completes.
        """
        for name, plugin in self._plugins.items():
            _logger.info("Starting plugin: %s", name)
            plugin.start()
            _logger.info("Plugin started: %s", name)

    def stop_all(self) -> None:
        """
        Call stop() on every registered plugin.

        Errors from individual plugins are caught and logged so that
        all plugins get a chance to stop cleanly.
        """
        for name, plugin in self._plugins.items():
            _logger.info("Stopping plugin: %s", name)
            try:
                plugin.stop()
                _logger.info("Plugin stopped: %s", name)
            except Exception as e:
                _logger.error("Error stopping plugin '%s': %s", name, e)
