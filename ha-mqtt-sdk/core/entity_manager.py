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
- sdk/core/sdk.py
"""

from .entity_factory import create_entity as _create_entity

from typing import Any, Callable, Dict, Optional

from ..models.entity import Entity
from ..config.domains import HADomain
from ..config.mqtt import MQTTSettings
from ..config.schemas import SCHEMAS
from ..builders.discovery_payload import build_discovery_payload
from ..builders.topic_manager import (
	build_discovery_topic,
	build_state_topic,
	build_command_topic,
	build_availability_topic,
)
from ..utils.logger import get_logger
from ..exceptions import CoreError

_logger = get_logger(__name__)

class EntityManager:
	def __init__(
		self,
		mqtt_client,
		mqtt_settings: MQTTSettings
	):
		"""
		Initialize EntityManager.

		Args:
			mqtt_client: MQTT client implementation
			mqtt_settings: MQTTSettings instance
		""" 

		if not mqtt_client:
			raise CoreError("mqtt_client is required")

		if not isinstance(
			mqtt_settings,
			MQTTSettings
		):
			raise CoreError("mqtt_settings must be MQTTSettings")

		self._mqtt = mqtt_client
		self._settings = mqtt_settings

		# Mapping command_topic -> callback
		self._command_callback: Dict[str, Callable[[str, Any], None]] = {}

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
		device_info: Optional[Any] = None,
		extra: Optional[Dict[str, Any]] = None,
	) -> Entity:
		"""
		Create an Entity with automatic topic generation.

		Used by:
		- SDK Users
		"""

		return _create_entity(
			domain = domain,
			name = name,
			unique_id = unique_id,
			discovery_prefix=self._settings.discovery_prefix,
			device_info = device_info,
			extra = extra,
		)

	def register(
		self,
		entity: Entity,
		command_callback: Optional[Callable[[str, Any], None]] = None,
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

		if not isinstance(entity: Entity):
			raise CoreError("Invalid entity")

		prefix = self._settings.discovery_prefix

		# -------------------------
		# Discovery
		# -------------------------

		discovery_topic = build_discovery_topic(
			entity.domain,
			entity.unique_id,
			prefix,
		)

		payload = build_discovery_payload(entity)

		self._mqtt.publish(
			topic = discovery_topic,
			payload = payload,
			retain = True,
		)

		_logger.info(
			"Entity registered: %s (%s)",
			entity.name,
			entity.domain.value,
		)

		# ------------------------
		# Last Will and Testament
		# ------------------------

		availability_topic = build_availability_topic(
			entity.domain,
			entity.unique_id,
			prefix,
		)

		if hasattr(self._mqtt, "set_last_will"):
			self._mqtt.set_last_will(availability_topic)
			_logger.debug("Last will registered for: %s", entity.unique_id)

		# -------------------------
		# Command handling
		# -------------------------

		if entity.command_topic:
			self._mqtt.subscribe(entity.command_topic)

			_logger.debug(
				"Subscribed to command topic: %s",
				entity.command_topic,
			)

			# Register callback if provided
			if command_callback:
				self._command_callbacks[entity.command_topic] = command_callback


	def update_state(
		self,
		entity: Entity,
		state: Any
	) -> None:
		"""
		Publish state update to MQTT.

		Args:
		entity: Entity instance
		state: State value (string, number, or JSON serializable)
		"""

		if not isinstance(entity: Entity):
			raise CoreError("Invalid entity")

		if not entity.state_topic:
			raise CoreError("Entity has no state_topic")

		self._mqtt.publish(
			topic = entity.state_topic,
			payload = state,
			retain = False,
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
			raise CoreError("Invalid entity")

		prefix = self._settings.discovery_prefix

		topic = build_availability_topic(
			entity.domain,
			entity.unique_id,
			prefix,
		)

		payload = "online" if online else "offline"

		self._mqtt.publish(
			topic = topic,
			payload = payload,
			retain = True, # IMPORTANT for HA
		)

		_logger.debug(
			"Availability updated: %s -> %s",
			entity.unique_id,
			payload,
		)

	def set_command_callback(
		self,
		entity: Entity,
		callback: Callable[[str, Any], None],
	) -> None:
		"""
		Set or update command callback for an entity.

		Args:
		entity: Entity instance
		callback: function(topic, payload)
		"""

		if not entity.command_topic:
			raise CoreError("Entity does not support commands")

		if not callable(callback):
			raise CoreError("callback must be callable")

		self._command_callbacks[entity.command_topic] = callback

		_logger.debug(
			"Command callback set for topic: %s",
			entity.command_topic,
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
