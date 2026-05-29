"""
Topic Manager

Responsible for building all MQTT topics for Home Assistant.

This module is fully independent of the MQTT transport layer.

Used by:
- sdk/core/entity_manager.py
"""

from ..config.domains import HADomain
from ..exceptions import BuilderError

def _validate_domain(domain: HADomain) -> None:
	if not isinstance(domain, HADomain):
		raise BuilderError("Invalid domain")


def _validate_unique_id(unique_id: str) -> None:
	if not unique_id or not isinstance(unique_id, str):
		raise BuilderError("unique_id must be a non-empty string")


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def build_discovery_topic(domain: HADomain, unique_id: str, prefix: str) -> str:
	"""
	Build Home Assistant discovery topic.

	Used by:
	- EntityManager.register()
	"""

	_validate_domain(domain)
	_validate_unique_id(unique_id)

	return f"{prefix}/{domain.value}/{unique_id}/config"


def build_state_topic(
	domain: HADomain,
	unique_id: str,
	prefix: str
) -> str:
	"""
	Build state topic.

	Used by:
	- EntityManager.update_state()
	"""

	_validate_domain(domain)
	_validate_unique_id(unique_id)

	return f"{prefix}/{domain.value}/{unique_id}/state"


def build_command_topic(domain: HADomain, unique_id: str, prefix: str,) -> str:
	"""
	Build command topic.

	Used by:
	- EntityManager.register()
	"""
	COMMANDABLE_DOMAINS = {
		HADomain.ALARM_CONTROL_PANEL,
		HADomain.BUTTON,
		HADomain.CLIMATE,
		HADomain.COVER,
		HADomain.DATE,
		HADomain.DATETIME,
		HADomain.FAN,
		HADomain.HUMIDIFIER,
		HADomain.LAWN_MOWER,
		HADomain.LIGHT,
		HADomain.LOCK,
		HADomain.NOTIFY,
		HADomain.NUMBER,
		HADomain.SCENE,
		HADomain.SELECT,
		HADomain.SIREN,
		HADomain.SWITCH,
		HADomain.TEXT,
		HADomain.TIME,
		HADomain.UPDATE,
		HADomain.VACUUM,
		HADomain.VALVE,
		HADomain.WATER_HEATER,
	}

	_validate_domain(domain)
	_validate_unique_id(unique_id)

	if domain not in COMMANDABLE_DOMAINS:
		return ""
	
	return f"{prefix}/{domain.value}/{unique_id}/set"

def build_availability_topic(
	domain,
	unique_id,
	prefix,
):
	return f"{prefix}/{domain.value}/{unique_id}/availability"
