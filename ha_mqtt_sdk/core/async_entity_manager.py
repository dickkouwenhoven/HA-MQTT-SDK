"""
async_entity_manager.py

Async version of EntityManager.

Used for asyncio-based integrations.
"""

from collections.abc import Awaitable, Callable
from typing import Any

from ..config.domains import HADomain
from ..config.mqtt import MQTTSettings
from ..exceptions import EntityError, ValidationError
from ..models.entity import Entity
from ..mqtt.async_client import AsyncMQTTClient
from ..utils.logger import get_logger
from .entity_factory import (
    build_registration,
)
from .entity_factory import (
    create_entity as _create_entity,
)

_logger = get_logger(__name__)


class AsyncEntityManager:
    def __init__(self, mqtt_client: AsyncMQTTClient, mqtt_settings: MQTTSettings):

        if not isinstance(
            mqtt_client,
            AsyncMQTTClient,
        ):
            raise ValidationError("mqtt_client must inherit from AsyncMQTTClient")

        if not isinstance(mqtt_settings, MQTTSettings):
            raise ValidationError("mqtt_settings must be MQTTSettings")

        self._mqtt = mqtt_client
        self._settings = mqtt_settings
        self._command_callbacks: dict[str, Callable[[str, str], Awaitable[None]]] = {}
        self._mqtt.set_message_callback(self._handle_command)

    def create_entity(
        self,
        domain: HADomain,
        name: str,
        unique_id: str,
        device_info: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> Entity:
        """
        Create an Entity with automatic topic generation.

        Used by:
        - SDK users (async path)
        """

        return _create_entity(
            domain=domain,
            name=name,
            unique_id=unique_id,
            device_info=device_info,
            extra=extra,
        )

    async def register(
        self, entity: Entity, command_callback: Callable[[str, str], Awaitable[None]] | None = None
    ) -> None:
        """
        Register entity in Home Assistant via MQTT discovery.

        Also:
        - Sets Last Will and Testament for availability
        - Subscribes to command topic (if applicable)

        Args:
                entity: Entity instance
        """

        if not isinstance(entity, Entity):
            raise EntityError("Invalid entity")

        # -----------------------------
        # Discovery
        # -----------------------------

        registration = build_registration(
            entity,
            self._settings.discovery_prefix,
        )

        await self._mqtt.publish(
            topic=registration.discovery_topic, payload=registration.discovery_payload, retain=True
        )

        _logger.info(
            "Entity registered: %s (%s)",
            entity.name,
            entity.domain.value,
        )

        # ------------------------
        # Last Will and Testament
        # ------------------------

        if hasattr(self._mqtt, "set_last_will"):
            self._mqtt.set_last_will(registration.availability_topic)
            _logger.debug("Last will registered for: %s", entity.unique_id)

        # ------------------------
        # Command handling
        # ------------------------

        if registration.command_topic:
            await self._mqtt.subscribe(registration.command_topic)

            _logger.debug(
                "Subscribed to command topic: %s",
                registration.command_topic,
            )

        if command_callback:
            self._command_callbacks[registration.command_topic] = command_callback

    async def update_state(self, entity: Entity, state: Any) -> None:

        if not isinstance(entity, Entity):
            raise EntityError("Invalid entity")

        registration = build_registration(
            entity,
            self._settings.discovery_prefix,
        )

        await self._mqtt.publish(
            topic=registration.state_topic,
            payload=state,
            retain=False,
        )

        _logger.debug(
            "State updated: %s -> %s",
            entity.unique_id,
            state,
        )

    async def update_availability(self, entity: Entity, online: bool) -> None:

        if not isinstance(entity, Entity):
            raise EntityError("Invalid entity")

        registration = build_registration(
            entity,
            self._settings.discovery_prefix,
        )

        payload = "online" if online else "offline"

        await self._mqtt.publish(
            topic=registration.availability_topic, payload=payload, retain=True
        )

        _logger.debug(
            "Availability updated: %s -> %s",
            entity.unique_id,
            payload,
        )

    def set_command_callback(
        self,
        entity: Entity,
        callback: Callable[[str, str], Awaitable[None]],
    ) -> None:
        """
        Set or update command callback for an entity.

        Args:
        entity: Entity instance
        callback: function(topic, payload)
        """

        if not isinstance(entity, Entity):
            raise EntityError("Invalid entity")

        if not callable(callback):
            raise EntityError("callback must be callable")

        registration = build_registration(
            entity,
            self._settings.discovery_prefix,
        )

        if not registration.command_topic:
            raise EntityError("Entity does not support commands")

        self._command_callbacks[registration.command_topic] = callback

        _logger.debug(
            "Command callback set for topic: %s",
            registration.command_topic,
        )

    async def _handle_command(self, topic: str, payload: Any) -> None:

        callback = self._command_callbacks.get(topic)

        if callback:
            await callback(topic, payload)
