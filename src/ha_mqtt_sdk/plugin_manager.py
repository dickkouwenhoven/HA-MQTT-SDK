"""
plugin_manager.py

Manages integration plugins.
"""

from .plugin_interface import IntegrationPlugin


class PluginManager:
    def __init__(self) -> None:
        self._plugins: dict[str, IntegrationPlugin] = {}

    def register_plugin(self, name: str, plugin: IntegrationPlugin) -> None:
        self._plugins[name] = plugin

    def get_plugin(self, name: str) -> IntegrationPlugin:
        return self._plugins[name]
