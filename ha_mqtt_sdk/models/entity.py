"""
entity.py

Represents a Home Assistant MQTT Entity.

Responsibilities:
- Hold entity configuration
- Validate against Home Assistant schema definitions

Used by:
- ha_mqtt_sdk/core/entity_manager.py
- ha_mqtt_sdk/builders/discovery_payload.py
"""

from typing import Optional, Dict, Any

from ..config.domains import HADomain
from ..config.device_fields import ALLOWED_FIELDS_PER_DOMAIN
from ..utils.logger import get_logger
from ..exceptions import EntityError

_logger = get_logger(__name__)


class Entity:
	def __init__(
		self,
		domain: HADomain,
		name: str,
		unique_id: str,
		device_info: Optional[Dict[str, Any]] = None,
		extra: Optional[Dict[str, Any]] = None,
	):
		self.domain = domain
		self.name = name
		self.unique_id = unique_id
		self.device_info = device_info
		self.extra = extra or {}

	# -----------------------------------------------------------------------
	# Public
	# -----------------------------------------------------------------------

	def validate(self) -> None:
		"""
		Validate entity against schema definitions.

		Used by:
		- discovery_payload.build_discovery_payload()
		"""

		self._validate_basic()
		self._validate_schema()


	def to_dict(self) -> Dict[str, Any]:
		payload = {
			"name": self.name,
			"unique_id": self.unique_id,
		}

		if self.device_info:
			payload["device"] = self.device_info

		payload.update(self.extra)

		return payload
	
	# -----------------------------------------------------------------------
	# Internal validation
	# -----------------------------------------------------------------------

	def _validate_basic(self) -> None:
		"""Basic type and value validation"""

		if not isinstance(self.domain, HADomain):
			raise EntityError("domain must be of type HADomain")

		if not isinstance(self.name, str) or not self.name.strip():
			raise EntityError("name must be a non-empty string")

		if not isinstance(self.unique_id, str) or not self.unique_id.strip():
			raise EntityError("unique_id must be a non-empty string")

		if self.extra and not isinstance(self.extra, dict):
			raise EntityError("extra must be a dictionary")

	def _validate_schema(self) -> None:
		"""Validate against HA schema"""

		schema = ALLOWED_FIELDS_PER_DOMAIN.get(
			self.domain
		)

		if not schema:
			raise EntityError(f"No schema defined for domain {self.domain}")

		# Build a virtual payload for validation
		payload_keys = {
			"name",
			"unique_id",
		}

		if self.device_info:
			payload_keys.add("device")

		if self.extra:
			payload_keys.update(self.extra.keys())

		# Check required fields
		missing = schema["required"] - payload_keys

		if missing:
			raise EntityError(
				f"{self.domain.value} missing required fields: {missing}"
			)

		# Strict mode
		allowed = (
			schema["required"]
			| schema["optional"]
		)
		invalid = payload_keys - allowed
		if invalid:
			raise EntityError(
				f"{self.domain.value} invalid fields: {invalid}"
			)

		_logger.debug(
			"Entity validated successfully: %s (%s)",
			self.name,
			self.domain.value,
		)
