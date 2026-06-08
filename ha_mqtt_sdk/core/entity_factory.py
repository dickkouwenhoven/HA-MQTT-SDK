"""
entity_factory.py

Share entity creation and registration preperation
for both EntityManager and AsyncEntityManager.

Responsibilities:
- Create entities
- Validate entities
- Build discovery payloads
- Build MQTT topic definitions

Used by:
- sdk/core/entity_manager.py
- sdk/core/async_entity_manager.py
"""

from dataclasses import dataclass
from typing import Any

from ..builders.discovery_payload import build_discovery_payload
from ..builders.topic_manager import (
	build_availability_topic,
	build_command_topic,
	build_discovery_topic,
	build_state_topic,
)
from ..config.domains import HADomain
from ..models.entity import Entity
from ..utils.logger import get_logger

_logger = get_logger(__name__)

@dataclass(slots=True)
class EntityRegistration:
	"""
	Pre-built MQTT registration information.

	Shared by sync and async entity managers.
	"""

	discovery_topic: str
	discovery_payload: dict[str, Any]

	state_topic: str
	command_topic: str
	availability_topic: str


def create_entity(
	domain: HADomain,
	name: str,
	unique_id: str,
	device_info: dict[str,Any] | None = None,
	extra: dict[str, Any] | None = None,
) -> Entity:
	"""
	Build an Entity with automatic topic generation.

	Shared by EntityManager and AsyncEntityManager.

	Args:
		domain: HADomain value
		name: Human-readable entity name
		unique_id: Unique identifier for the entity
		device_info: Optional device info block
		extra: Optional extra HA fields

	Returns:
		Entity: Fully constructed entity instance
	"""

	entity = Entity(
		domain=domain,
		name=name,
		unique_id=unique_id,
		device_info=device_info,
		extra=extra,
	)

	entity.validate()

	_logger.debug("Entity created and validated: %s (%s)", name, domain.value)

	return entity

def build_registration(
	entity: Entity,
	discovery_prefix: str,
) -> EntityRegistration:
	"""
	Build all MQTT topic and discovery payload
	for an entity.

	This function contains all share logic used by both EntityManager and AsyncEntityManager.
	"""

	entity.validate()

	discovery_topic = build_discovery_topic(
		entity.domain,
		entity.unique_id,
		discovery_prefix,
	)

	discovery_payload = build_discovery_payload(
		entity,
		discovery_prefix,
	)

	state_topic = build_state_topic(
		entity.domain,
		entity.unique_id,
		discovery_prefix,
	)

	command_topic = build_command_topic(
		entity.domain,
		entity.unique_id,
		discovery_prefix,
	)

	availability_topic = build_availability_topic(
		entity.domain,
		entity.unique_id,
		discovery_prefix,
	)

	return EntityRegistration(
		discovery_topic=discovery_topic,
		discovery_payload=discovery_payload,
		state_topic=state_topic,
		command_topic=command_topic,
		availability_topic=availability_topic,
	)
