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

from .entity_factory import (
	create_entity as _create_entity,
	build_registration
)

from typing import Any, Callable, Dict, Optional

from ..models.entity import Entity
from ..config.domains import HADomain
from ..config.mqtt import MQTTSettings
)
from ..mqtt.paho_client import PahoMQTTClient
from ..utils.logger import get_logger
from ..exceptions import EntityError

_logger = get_logger(__name__)

class EntityManager:
	def __init__(
		self,
		mqtt_client: PahoMQTTClient,
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
			PahoMQTTClient,
		):
			raise EntityError("mqtt_client must inherit from PahoMQTTClient")

		if not isinstance(
			mqtt_settings,
			MQTTSettings
		):
			raise EntityError("mqtt_settings must be MQTTSettings")

		self._mqtt = mqtt_client
		self._settings = mqtt_settings

		# Mapping command_topic -> callback
		self._command_callbacks: Dict[str, Callable[[str, str], None]] = {}

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
		device_info: Optional[Dict[str,Any]] = None,
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
			device_info = device_info,
			extra = extra,
		)

	def register(
		self,
		entity: Entity,
		command_callback: Optional[Callable[[str, str], None]] = None,
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

		registration = build_registration(
			entity,
			self._settings.discovery_prefix,
		)

		# -------------------------
		# Discovery
		# -------------------------

		self._mqtt.publish(
			topic = registration.discovery_topic,
			payload = registration.discovery_payload,
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

		if hasattr(self._mqtt, "set_last_will"):
			self._mqtt.set_last_will(
				registration.availability_topic
			)
			_logger.debug("Last will registered for: %s", entity.unique_id)

		# -------------------------
		# Command handling
		# -------------------------

		if registration.command_topic:
			self._mqtt.subscribe(
				registration.command_topic
			)
	
			_logger.debug(
				"Subscribed to command topic: %s",
				registration.command_topic,
			)

		# Register callback if provided
		if command_callback:
			self._command_callbacks[
				registration.command_topic
			] = command_callback


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

		if not isinstance(entity, Entity):
			raise EntityError("Invalid entity")

		registration = build_registration(
			entity,
			self._settings.discovery_prefix,
		)

		self._mqtt.publish(
			topic = registration.state_topic,
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
			raise EntityError("Invalid entity")

		registration = build_registration(
			entity,
			self._settings.discovery_prefix,
		)

		payload = "online" if online else "offline"

		self._mqtt.publish(
			topic = registration.availability_topic,
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
		callback: Callable[[str, str], None],
	) -> None:
		"""
		Set or update command callback for an entity.

		Args:
		entity: Entity instance
		callback: function(topic, payload)
		"""

		registration = build_registration(
			entity,
			self._settings.discovery_prefix,
		)
		
		if not registration.command_topic:
			raise EntityError("Entity does not support commands")

		if not callable(callback):
			raise EntityError("callback must be callable")

		self._command_callbacks[
			registration.command_topic
		] = callback

		_logger.debug(
			"Command callback set for topic: %s",
			topic,
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
