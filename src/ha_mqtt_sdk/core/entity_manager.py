"""
High-level orchestration layer for mapping Home Assistant entities.

Responsibilities:
- Create entities with automatic topic generation
- Register entities via MQTT discovery
- Publish state updates
- Publish availability (online/offline)
- Handle incoming MQTT commands from Home Assistant

Design principles:
- SDK user should NOT deal with topics
- All MQTT topic logic is centralized here
- Builders only transform, never decide

Used by:
- ha_mqtt_sdk/core/sdk.py
"""

from collections.abc import Callable
from typing import Any

from ..config.domains import HADomain
from ..config.mqtt import MQTTSettings
from ..exceptions import EntityError
from ..models.device_info import DeviceInfo
from ..models.entity import Entity
from ..mqtt.base import BaseMQTTClient
from ..types import StateValue
from ..utils.logger import get_logger
from .entity_factory import build_registration
from .entity_factory import create_entity as _create_entity

_logger = get_logger(__name__)


class EntityManager:
    def __init__(
        self,
        mqtt_client: BaseMQTTClient,
        mqtt_settings: MQTTSettings,
    ):
        """
        Initialize EntityManager.

        Args:
                mqtt_client: MQTT client implementation
                mqtt_settings: MQTTSettings instance
        """

        if not isinstance(
            mqtt_client,
            BaseMQTTClient,
        ):
            raise EntityError("mqtt_client must inherit from BaseMQTTClient")

        if not isinstance(mqtt_settings, MQTTSettings):
            raise EntityError("mqtt_settings must be MQTTSettings")

        self._mqtt = mqtt_client
        self._settings = mqtt_settings

        # Mapping command_topic -> callback
        self._command_callbacks: dict[str, Callable[[str, str], None]] = {}
        self._entities: dict[str, Entity] = {}

        # Register global MQTT message handler
        self._mqtt.set_message_callback(self._handle_command)

    # -------------------------
    # PUBLIC API
    # -------------------------

    def create_entity(
        self,
        domain: HADomain,
        name: str,
        unique_id: str,
        device_info: DeviceInfo | None = None,
        extra: dict[str, Any] | None = None,
    ) -> Entity:
        """
        Create an Entity with automatic topic generation.

        Used by:
        - SDK Users
        """

        return _create_entity(
            domain=domain,
            name=name,
            unique_id=unique_id,
            device_info=device_info,
            extra=extra,
        )

    def register(
        self,
        entity: Entity,
        command_callback: Callable[[str, str], None] | None = None,
    ) -> None:
        """
        Register entity in Home Assistant via MQTT discovery.

        Also:
        - Sets Last Will and Testament for availability
        - Subscribers to command topic (if applicable)
        - Registers callback for incoming commands

        Args:
        entity: Entity instance
        command_callback: Optional handler for commands
        """

        if not isinstance(entity, Entity):
            raise EntityError("Invalid entity")

        if entity.unique_id in self._entities:
            raise EntityError(f"Entity with unique_id '{entity.unique_id}' is already registered")

        registration = build_registration(
            entity,
            self._settings.discovery_prefix,
        )

        # -------------------------
        # Discovery
        # -------------------------

        self._mqtt.publish(
            topic=registration.discovery_topic,
            payload=registration.discovery_payload,
            retain=True,
        )

        self._entities[entity.unique_id] = entity

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

        # -------------------------
        # Command handling
        # -------------------------

        if registration.command_topic:
            self._mqtt.subscribe(registration.command_topic)

            _logger.debug(
                "Subscribed to command topic: %s",
                registration.command_topic,
            )

            # Register callback if provided
            if command_callback:
                self._command_callbacks[registration.command_topic] = command_callback

    def update_state(self, entity: Entity, state: StateValue) -> None:
        """
        Publish state update to MQTT.

        Args:
        entity: Entity instance
        state: State value (string, number, or JSON serializable)
        """

        if not isinstance(entity, Entity):
            raise EntityError("Invalid entity")

        if entity.unique_id not in self._entities:
            raise EntityError(f"Entity '{entity.unique_id}' is not registered")

        registration = build_registration(
            entity,
            self._settings.discovery_prefix,
        )

        if registration.state_topic is None:
            raise EntityError(
                f"Entity domain '{entity.domain.value}' does not support state updates"
            )

        self._mqtt.publish(
            topic=registration.state_topic,
            payload=state,
            retain=False,
        )

        _logger.debug(
            "State updated: %s -> %s",
            entity.unique_id,
            state,
        )

    def update_availability(
        self,
        entity: Entity,
        online: bool,
    ) -> None:
        """
        Publish availability (online/offline) to MQTT.

        This control whether the device is shown as available in Home Assistant.

        Args:
        entity: Entity instance
        online: True= online, False = offline
        """

        if not isinstance(entity, Entity):
            raise EntityError("Invalid entity")

        if entity.unique_id not in self._entities:
            raise EntityError(f"Entity '{entity.unique_id}' is not registered")

        registration = build_registration(
            entity,
            self._settings.discovery_prefix,
        )

        if registration.availability_topic is None:
            raise EntityError(
                f"Entity domain '{entity.domain.value} ' does not support availability updates"
            ) 

        payload = "online" if online else "offline"

        self._mqtt.publish(
            topic=registration.availability_topic,
            payload=payload,
            retain=True,  # IMPORTANT for HA
        )

        _logger.debug(
            "Availability updated: %s -> %s",
            entity.unique_id,
            payload,
        )

    def set_command_callback(
        self,
        entity: Entity,
        callback: Callable[[str, str], None],
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

        if entity.unique_id not in self._entities:
            raise EntityError(f"Entity '{entity.unique_id}' is not registered")

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

    # -------------------------
    # Internal
    # -------------------------

    def _handle_command(
        self,
        topic: str,
        payload: Any,
    ) -> None:
        """
        Internal MQTT message handler.

        Called by MQTT client when a message is received.

        Routes incoming commands to registered callbacks.
        """

        _logger.debug(
            "Command received:%s -> %s",
            topic,
            payload,
        )

        callback = self._command_callbacks.get(topic)

        if not callback:
            _logger.warning(
                "No callback registered for topic: %s",
                topic,
            )
            return

        try:
            callback(topic, payload)
        except Exception as e:
            _logger.error(
                "Error handling command for %s: %s",
                topic,
                str(e),
            )

    def is_registered(
        self,
        entity: Entity,
    ) -> bool:
        if not isinstance(entity, Entity):
            raise EntityError("Invalid entity")

        return entity.unique_id in self._entities

    def get_entity(
        self,
        unique_id: str,
    ) -> Entity | None:
        """
        Get registered entity by unique_id.

        Args:
        unique_id: Entity unique_id

        Returns:
        Entity instance or None
        """

        if not isinstance(unique_id, str) or not unique_id.strip():
            raise EntityError("unique_id must be a non-empty string")

        return self._entities.get(unique_id)

    def unregister(
        self,
        entity: Entity,
    ) -> None:
        """
        Remove entity from manager registry.

        Args:
        entity: Entity instance
        """

        if not isinstance(entity, Entity):
            raise EntityError("Invalid entity")

        if entity.unique_id not in self._entities:
            raise EntityError(f"Entity '{entity.unique_id}' is not registered")

        registration = build_registration(
            entity,
            self._settings.discovery_prefix,
        )

        # Remove entity from Home Assistant
        self._mqtt.publish(
            topic=registration.discovery_topic,
            payload="",
            retain=True,
        )

        # Remove callback
        if registration.command_topic:
            self._command_callbacks.pop(
                registration.command_topic,
                None,
            )

        # Remove entity from registry
        del self._entities[entity.unique_id]

        _logger.info(
            "Entity unregistered: %s",
            entity.unique_id,
        )
