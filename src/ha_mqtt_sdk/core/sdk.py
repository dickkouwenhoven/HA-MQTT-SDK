"""
HASDK - High-level orchestration entrypoint.

This is the main interface for users of the SDK.

Responsibilities:
- Initialize MQTT client (or accept injected client)
- Manage entity lifecycle via EntityManager
- Provide simple API for:
    - register
    - state updates
    - command handling

Used by:
- End users of the SDK
"""

from collections.abc import Callable
from typing import Any

from ..config.domains import HADomain
from ..config.mqtt import MQTTSettings
from ..exceptions import SDKError
from ..models.device_info import DeviceInfo
from ..models.entity import Entity
from ..mqtt import PahoMQTTClient
from ..types import StateValue
from ..utils.logger import get_logger
from .entity_factory import create_entity as _create_entity
from .entity_manager import EntityManager
from .plugin_interface import IntegrationPlugin
from .plugin_manager import PluginManager


class HASDK:
    def __init__(
        self,
        mqtt_client: PahoMQTTClient | None = None,
        mqtt_settings: MQTTSettings | None = None,
    ):
        """
        Initialize SDK.

        Either mqtt_settings OR mqtt_client must be provided.
        """

        self._logger = get_logger(__name__)
        self._mqtt_settings = mqtt_settings or MQTTSettings()

        if not mqtt_client and not mqtt_settings:
            raise SDKError("Provide either mqtt_settings or mqtt_client")

        if mqtt_client and mqtt_settings:
            self._logger.warning("Both mqtt_client and mqtt_settings provided. Using mqtt_client.")

        # Dependency injection (preferred)
        if mqtt_client:
            self._mqtt = mqtt_client
        else:
            assert mqtt_settings is not None
            self._mqtt = PahoMQTTClient(mqtt_settings)

        self._entity_manager = EntityManager(self._mqtt, self._mqtt_settings)

    # -------------------------
    # Public API
    # -------------------------

    def start(self) -> None:
        """
        Start MQTT connection.
        """
        self._logger.info("Starting HASDK")
        self._mqtt.connect()

    def register(
        self, entity: Entity, command_callback: Callable[[str, str], None] | None = None
    ) -> None:
        """
        Register entity in Home Assistant.

        Used by:
        - user code
        """
        if not isinstance(entity, Entity):
            raise SDKError("Invalid entity")

        self._entity_manager.register(entity, command_callback)

    def update_state(self, entity: Entity, state: StateValue) -> None:
        """
        Update entity state.

        Used by:
        - user code
        """
        if not isinstance(entity, Entity):
            raise SDKError("Invalid entity")

        self._entity_manager.update_state(entity, state)

    def on_command(self, entity: Entity, callback: Callable[[str, str], None]) -> None:
        """
        Register global command handler.

        Used by:
        - user code (Dirigera integration)
        """
        if not isinstance(entity, Entity):
            raise SDKError("Invalid entity")

        if not callable(callback):
            raise SDKError("Callback must be callable")

        self._entity_manager.set_command_callback(entity, callback)

    def create_entity(
        self,
        *,
        domain: HADomain,
        name: str,
        unique_id: str,
        device_info: DeviceInfo | None = None,
        extra: dict[str, Any] | None = None,
    ) -> Entity:
        return _create_entity(
            domain=domain,
            name=name,
            unique_id=unique_id,
            device_info=device_info,
            extra=extra,
        )

    def unregister(
        self,
        entity: Entity,
    ) -> None:
        self._entity_manager.unregister(entity)

    def is_registered(
        self,
        entity: Entity,
    ) -> bool:
        return self._entity_manager.is_registered(entity)

    def use_plugin(self, name: str, plugin: IntegrationPlugin) -> None:
        """Register an integration plugin."""

        if not hasattr(self, "_plugin_manager"):
            self._plugin_manager = PluginManager(self)
        self._plugin_manager.register(name, plugin)

    def run(self) -> None:
        """Full lifecycle entry point for plugin-based applications."""
    
        self.start()
        if hasattr(self, "_plugin_manager"):
            self._plugin_manager.setup_all()
            self._plugin_manager.start_all()

    def shutdown(self) -> None:
        if hasattr(self, "_plugin_manager"):
            self._plugin_manager.stop_all()
        self._logger.info("Shutting down HASDK")
        self._mqtt.disconnect()
