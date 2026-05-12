"""
plugin_manager.py

Manages integration plugins.
"""

from typing import Dict

from .plugin_interface import IntegrationPlugin


class PluginManager:

	def __init__(self):
		self._plugins: Dict[str, IntegrationPlugin] = {}

	def register_plugin(self, name: str, plugin: IntegrationPlugin):
		self._plugins[name] = plugin

	def get_plugin(self, name: str) -> IntegrationPlugin:
		return self._plugins[name]
