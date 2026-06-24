"""
AsyncHASDK - High-level orchestration entrypoint for asynchronice communication.

This is the main interface for users of the Async version of the SDK.

Responsibilities:
- Initialize Async MQTT client (aiomqtt or accept injected client)
- Manage entity lifecycle via AsyncEntityManager
- Provide simple API for:
    - register
    - state updates
    - command handling

Used by:
- End users of the Async version of the SDK
"""

from collections.abc import Awaitable, Callable
from typing import Any

from ..config.domains import HADomain
from ..config.mqtt import MQTTSettings
from ..exceptions import SDKError
from ..models.device_info import DeviceInfo
from ..models.entity import Entity
from ..mqtt import AsyncMQTTClient
from ..types import StateValue
from ..utils.logger import get_logger
from .async_entity_manager import AsyncEntityManager
from .async_plugin_interface import AsyncIntegrationPlugin
from .async_plugin_manager import AsyncPluginManager


class AsyncHASDK:
    def __init__(
        self,
        async_mqtt_client: AsyncMQTTClient | None = None,
        mqtt_settings: MQTTSettings | None = None,
    ):
        """
        Initialize async SDK.

        Either mqtt_settings OR async_mqtt_client must be provided.
        """

        self._logger = get_logger(__name__)
        self._mqtt_settings = mqtt_settings or MQTTSettings()

        if not async_mqtt_client and not mqtt_settings:
            raise SDKError("Provide either mqtt_settings or async_mqtt_client")

        if async_mqtt_client and mqtt_settings:
            self._logger.warning(
                "Both async_mqtt_client and mqtt_settings provided. Using async_mqtt_client."
            )

        # Dependency injection (preferred)
        if async_mqtt_client:
            self._mqtt = async_mqtt_client
        else:
            assert mqtt_settings is not None
            self._mqtt = AsyncMQTTClient(mqtt_settings)

        self._async_entity_manager = AsyncEntityManager(self._mqtt, self._mqtt_settings)

    # -------------------------
    # Public API
    # -------------------------

    async def start(self) -> None:
        """
        Start MQTT connection.
        """
        self._logger.info("Starting AsyncHASDK")
        await self._mqtt.connect()

    async def register(
        self, entity: Entity, command_callback: Callable[[str, str], Awaitable[None]] | None = None
    ) -> None:
        """
        Register entity in Home Assistant.

        Used by:
        - user code
        """
        if not isinstance(entity, Entity):
            raise SDKError("Invalid entity")

        await self._async_entity_manager.register(entity, command_callback)

    async def update_state(self, entity: Entity, state: StateValue) -> None:
        """
        Update entity state.

        Used by:
        - user code
        """
        if not isinstance(entity, Entity):
            raise SDKError("Invalid entity")

        await self._async_entity_manager.update_state(entity, state)

    async def on_command(
        self, entity: Entity, callback: Callable[[str, str], Awaitable[None]]
    ) -> None:
        """
        Register global command handler.

        Used by:
        - user code (Dirigera integration)
        """
        if not isinstance(entity, Entity):
            raise SDKError("Invalid entity")

        if not callable(callback):
            raise SDKError("Callback must be callable")

        await self._async_entity_manager.set_command_callback(entity, callback)

    def create_entity(
        self,
        *,
        domain: HADomain,
        name: str,
        unique_id: str,
        device_info: DeviceInfo | None = None,
        extra: dict[str, Any] | None = None,
    ) -> Entity:
        return self._async_entity_manager.create_entity(
            domain=domain,
            name=name,
            unique_id=unique_id,
            device_info=device_info,
            extra=extra,
        )

    async def unregister(
        self,
        entity: Entity,
    ) -> None:
        await self._async_entity_manager.unregister(entity)

    def is_registered(
        self,
        entity: Entity,
    ) -> bool:
        return self._async_entity_manager.is_registered(entity)

    def use_plugin(self, name: str, plugin: AsyncIntegrationPlugin) -> None:
        """Register an async integration plugin."""

        if not hasattr(self, "_plugin_manager"):
            self._plugin_manager = AsyncPluginManager(self)
        self._plugin_manager.register(name, plugin)

    async def run(self) -> None:
        """Full lifecycle entry point for plugin-based applications."""

        await self.start()
        if hasattr(self, "_plugin_manager"):
            await self._plugin_manager.setup_all()
            await self._plugin_manager.start_all()

    async def shutdown(self) -> None:
        if hasattr(self, "_plugin_manager"):
            await self._plugin_manager.stop_all()
        self._logger.info("Shutting down AsyncHASDK")
        await self._mqtt.disconnect()
