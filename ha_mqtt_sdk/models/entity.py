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

from .device_info import DeviceInfo
from ..config.domains import HADomain
from ..config.device_fields import ALLOWED_FIELDS_PER_DOMAIN
from ..utils.logger import get_logger
from ..exceptions import EntityError, SchemaError

_logger = get_logger(__name__)


class Entity:
	def __init__(
		self,
		domain: HADomain,
		name: str,
		unique_id: str,
		device_info: Optional[DeviceInfo] = None,
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

	def _validate_tuple_collection(
		self,
		items: list[tuple[str, str]],
		field_name: str,
	) -> None:
		if not isinstance(items, list):
			raise EntityError(
				f"device_info {field_name} must be a list"
			)

		for item in items:
			if (
				not isinstance(item, tuple)
				or len(item) != 2
			):
				raise EntityError(
					f"device_info {field_name} must contain 2-item tuples"
				)
			
			key, value = item

			if (
				not isinstance(key, str)
				or not key.strip()
			):
				raise EntityError(
					f"device_info {field_name} key must be a non-empty string"
				)

			if (
				not isinstance(value, str)
				or not value.strip()
			):
				raise EntityError(
					f"device_info {field_name} value must be a non-empty string"
				)
				
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

		# -----------------------------------------------------------------------
		# Device Info validation
		# -----------------------------------------------------------------------

		if self.device_info is not None:

			if not isinstance(self.device_info, dict):
				raise EntityError(
					"device_info must be a dictionary"
				)
			
			if not any(
				key in self.device_info
				for key in ("identifiers", "connections")
			):
				raise EntityError(
					"At least one of 'identifiers' or 'connections' must be provided"
				)
			
			if "identifiers" in self.device_info:
				self._validate_tuple_collection(
					self.device_info["identifiers"],
					"identifiers",
				)

			if "connections"in self.device_info:
				self._validate_tuple_collection(
					self.device_info["connections"],
					"connections",
				)

			# How to handle via_device, because it is tuple[str, str]?
			string_fields = (
				"manufacturer",
				"model",
				"name",
				"sw_version",
				"hw_version",
				"suggested_area",
				"configuration",
				"serial_number",
				"model_id",
			)

			for field in string_fields:

				value = self.device_info.get(field)

				if value is None:
					continue

				if not isinstance(value, str):
					raise EntityError(
						f"device_info field '{field}' must be a string"
					)

				if not value.strip():
					raise EntityError(
						f"device_info field '{field}' cannot be empty"
					)
						
		

	def _validate_schema(self) -> None:
		"""Validate extra fields against HA domain definitions."""

		schema = ALLOWED_FIELDS_PER_DOMAIN.get(
			self.domain
		)

		if not schema:
			raise SchemaError(f"No field definition for domain {self.domain}")

		allowed = (
			schema["required"]
			| schema["optional"]
		)

		allowed.update({
			"name",
			"unique_id",
			"device",
		})
		
		invalid = set(
			(self.extra or {}).keys()
		) - allowed
		
		if invalid:
			raise SchemaError(
				f"{self.domain.value} invalid fields: {invalid}"
			)
		
		_logger.debug(
			"Entity validated successfully: %s (%s)",
			self.name,
			self.domain.value,
		)
