"""
plugin_interface.py

Defines interface for SDK plugins (integrations).
"""

from abc import ABC, abstractmethod
from typing import Any

from .models.entity import Entity


class IntegrationPlugin(ABC):
    @abstractmethod
    def map_device(self, data: Any, entity_manager) -> list[Entity]:
        """Map device data to entities"""
        pass

    @abstractmethod
    def handle_command(self, topic: str, payload: Any) -> None:
        """Handle incoming command"""
        pass
