"""
Discovery Payload Builder

Responsible for building Home Assistant MQTT discovery payloads.

This module:
- Translates Entity → HA payload

Used by:
- sdk/core/entity_manager.py
"""

from typing import Dict, Any

from ..models.entity import Entity
from ..validators.payload_validator import validate_discovery_payload 
from ..utils.logger import get_logger
from .topic_manager import (
	build_state_topic,
	build_command_topic,
)
from ..exceptions import EntityError


_logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_entity(entity: Entity) -> None:
	if not isinstance(entity, Entity):
		raise EntityError("Invalid entity")


def _build_device_block(entity: Entity) -> Dict[str, Any]:
	"""
	Build device block for HA.
	"""

	_validate_entity(entity)
	entity.validate()
	
	if not entity.device_info:
		return {}

	return dict(entity.device_info)


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def build_discovery_payload(
	entity: Entity,
	prefix: str,
) -> Dict[str, Any]:
	"""
	Build full Home Assistant MQTT discovery payload.

	Responsibilities:
	- Build HA-compatible discovery payload
	- Add optional device block
	- Merge extra attributes
	
	Used by:
	- EntityManager.register()
	"""

	_validate_entity(entity)
	entity.validate()

	# ------------------------------------------------------
	# Base payload
	# ------------------------------------------------------
	
	payload: Dict[str, Any] = {
		"name": entity.name,
		"unique_id": entity.unique_id,
		"state_topic": build_state_topic(
			entity.domain, 
			entity.unique_id, 
			prefix,
		)
	}
	
	# ------------------------------------------------------
	# Optional command topic
	# ------------------------------------------------------
	
	command_topic = build_command_topic(
		entity.domain,
		entity.unique_id,
		prefix,
	)

	if command_topic:
		payload["command_topic"] = command_topic

	# ------------------------------------------------------
	# Optional device block
	# ------------------------------------------------------
	
	device_block = _build_device_block(entity)
	
	if device_block:
		payload["device"] = device_block

	# ------------------------------------------------------
	# Extra user-defined attributes
	# ------------------------------------------------------
	
	if entity.extra:
		payload.update(entity.extra)

	# ------------------------------------------------------
	# Payload validation
	# ------------------------------------------------------
	validate_discovery_payload(
		payload=payload,
		domain=entity.domain,
	)

	# ------------------------------------------------------
	# Logging
	# ------------------------------------------------------
	
	_logger.debug(
		"Discovery payload built for %s: %s",
		entity.name,
		entity.unique_id,
	)

	return payload
