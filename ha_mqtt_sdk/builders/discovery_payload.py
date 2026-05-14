"""
Discovery Payload Builder

Responsible for building Home Assistant MQTT discovery payloads.

This module:
- Translates Entity → HA payload
- Validates against schemas

Used by:
- sdk/core/entity_manager.py
"""

from typing import Dict, Any

from ..models.entity import Entity
from ..config.schemas import SCHEMAS
from ..utils.logger import get_logger
from .topic_manager import (
	build_state_topic,
	build_command_topic,
)
from ..exceptions import BuilderError, EntityError


_logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_entity(entity: Entity) -> None:
	if not isinstance(entity, Entity):
		raise EntityError("Invalid entity")


def _validate_schema(entity: Entity, payload: Dict[str, Any]) -> None:
	"""
	Validate payload against schema definition.
	"""

	schema = SCHEMAS.get(entity.domain)

	if not schema:
		raise BuilderError(f"No schema found for domain {entity.domain}")

	missing = schema.required_fields - payload.keys()

	if missing:
		raise BuilderError(
			f"Missing required fields for {entity.domain.value}: {missing}"
		)


def _build_device_block(entity: Entity) -> Dict[str, Any]:
	"""
	Build device block for HA.
	"""

	device = entity.device_info

	if not device:
		return {}

	return {
		"identifiers": device.identifiers,
		"manufacturer": device.manufacturer,
		"model": device.model,
		"name": device.name,
		"sw_version": device.sw_version,
		"hw_version": device.hw_version,
	}


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def build_discovery_payload(
	entity: Entity,
	prefix: str,
) -> Dict[str, Any]:
	"""
	Build full discovery payload for Home Assistant.

	Used by:
	- EntityManager.register()
	"""

	_validate_entity(entity)

	payload: Dict[str, Any] = {
		"name": entity.name,
		"unique_id": entity.unique_id,
		"state_topic": build_state_topic(
				entity.domain, 
				entity.unique_id, 
				prefix,
			),
	}

	command_topic = build_command_topic(
		entity.domain,
		entity.unique_id,
		prefix,
	)
	payload = {
		"name": entity.name,
		"unique_id": entity.unique_id,
		"command_topic": command_topic,
	}

	# Device block
	device_block = _build_device_block(entity)
	if device_block:
		payload["device"] = device_block

	# Extra attributes (flexibility)
	if entity.extra:
		payload.update(entity.extra)

	# Validate against schema
	_validate_schema(entity, payload)

	_logger.debug(
		"Discovery payload built for %s: %s",
		entity.unique_id,
		payload,
	)

	return payload
