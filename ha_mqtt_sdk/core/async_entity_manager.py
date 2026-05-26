"""
async_entity_manager.py

Async version of EntityManager.

Used for asyncio-based integrations.
"""

from typing import Optional, Dict, Any, Callable, Awaitable

from .entity_factory import create_entity as _create_entity

from ..models.entity import Entity
from ..config.domains import HADomain
from ..config.mqtt import MQTTSettings
from ..config.schemas import SCHEMAS
from ..builders.discovery_payload import build_discovery_payload
from ..builders.topic_manager import (
	build_discovery_topic,
	build_command_topic,
	build_availability_topic,
	build_state_topic,
)
from ..mqtt.base import BaseMQTTClient
from ..utils.logger import get_logger
from ..exceptions  import CoreError, MQTTError

_logger = get_logger(__name__)

class AsyncEntityManager:
	def __init__(self, mqtt_client: BaseMQTTClient, mqtt_settings: MQTTSettings):

		if not isinstance(
			mqtt_client,
			BaseMQTTClient,
		):
			raise CoreError("mqtt_client must inherit from BaseMQTTClient")

		if not isinstance(
			mqtt_settings,
			MQTTSettings
		):
			raise CoreError("mqtt_settings must be MQTTSettings")
				
		self._mqtt = mqtt_client
		self._settings = mqtt_settings
		self._command_callbacks: Dict[str, Callable[[str, str], Awaitable[None]]] = {}
		self._mqtt.set_message_callback(self._handle_command)

	async def create_entity(
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
		- SDK users (async path)
		"""

		return _create_entity(
			domain=domain,
			name=name,
			unique_id=unique_id,
			device_info=device_info,
			extra=extra,
		)

	async def register(self, entity: Entity) -> None:
		"""
		Register entity in Home Assistant via MQTT discovery.

		Also:
		- Sets Last Will and Testament for availability
		- Subscribes to command topic (if applicable)

		Args:
			entity: Entity instance
		"""

		if not isinstance(entity, Entity):
			raise CoreError("Invalid entity")

		# -----------------------------
		# Discovery
		# -----------------------------

		topic = build_discovery_topic(
			entity.domain,
			entity.unique_id,
			self._settings.discovery_prefix,
		)

		payload = build_discovery_payload(
			entity,
			self._settings.discovery_prefix,
		)

		await self._mqtt.publish(topic, payload, retain=True)

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
			self._settings.discovery_prefix,
		)

		if hasattr(self._mqtt, "set_last_will"):
			self._mqtt.set_last_will(availability_topic)
			_logger.debug("Last will registered for: %s", entity.unique_id)

		# ------------------------
		# Command handling
		# ------------------------

		# if entity.command_topic:
		# 	await self._mqtt.subscribe(entity.command_topic)
		topic = build_command_topic(
			entity.domain,
			entity.unique_id,
			self._settings.discovery_prefix,
		)

		await self._mqtt.subscribe(topic)

	async def update_state(self, entity: Entity, state: Any) -> None:
		topic = build_state_topic(
			entity.domain,
			entity.unique_id,
			self._settings.discovery_prefix,
		)
		await self._mqtt.publish(topic, state)

	async def update_availability(self, entity: Entity, online: bool) -> None:

		topic = build_availability_topic(
			entity.domain,
			entity.unique_id,
			self._settings.discovery_prefix,
		)

		payload = "online" if online else "offline"

		await self._mqtt.publish(topic, payload, retain=True)

	async def _handle_command(self, topic: str, payload: Any) -> None:

		callback = self._command_callbacks.get(topic)

		if callback:
			await callback(topic, payload)
