"""
entity_factory.py

Share entity creation for both EntityManager and AsyncEntityManager.

Responsibilities:
- Validate inputs
- Build topics
- Construct and return an Entity instance

Used by:
- sdk/core/entity_manager.py
- sdk/core/async_entity_manager.py
"""

from typing import Any, Dict, Optional

from ..models.entity import Entity
from ..config.domains import HADomain
from ..utils.logger import get_logger

_logger = get_logger(__name__)

def create_entity(
	domain: HADomain,
	name: str,
	unique_id: str,
	device_info: Optional[Dict[str,Any]] = None,
	extra: Optional[Dict[str, Any]] = None,
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
