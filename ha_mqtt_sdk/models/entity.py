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
from ..config.schemas import SCHEMAS
from ..utils.logger import get_logger
from ..exceptions import EntityError

_logger = get_logger(__name__)


class Entity:
	def __init__(
		self,
		domain: HADomain,
		name: str,
		unique_id: str,
		state_topic: Optional[str] = None,
		command_topic: Optional[str] = None,
		device_info: Optional[Any] = None,
		extra: Optional[Dict[str, Any]] = None,
	):
		self.domain = domain
		self.name = name
		self.unique_id = unique_id

		self.state_topic = state_topic
		self.command_topic = command_topic

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

		if self.state_topic:
			payload["state_topic"] = self.state_topic

		if self.command_topic:
			payload["command_topic"] = self.command_topic

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

		if self.state_topic and not isinstance(self.state_topic, str):
			raise EntityError("state_topic must be a string")

		if self.command_topic and not isinstance(self.command_topic, str):
			raise EntityError("command_topic must be a string")

		if self.extra and not isinstance(self.extra, dict):
			raise EntityError("extra must be a dictionary")

	def _validate_schema(self) -> None:
		"""Validate against HA schema"""

		schema = SCHEMAS.get(self.domain)

		if not schema:
			raise EntityError(f"No schema defined for domain {self.domain}")

		# Build a virtual payload for validation
		payload_keys = {
			"name",
			"unique_id",
		}

		if self.state_topic:
			payload_keys.add("state_topic")

		if self.command_topic:
			payload_keys.add("command_topic")

		if self.device_info:
			payload_keys.add("device")

		if self.extra:
			payload_keys.update(self.extra.keys())

		# Check required fields
		missing = schema.required_fields - payload_keys

		if missing:
			raise EntityError(
				f"{self.domain.value} missing required fields: {missing}"
			)

		# Strict mode
		allowed = schema.required_fields | schema.optional_fields
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
