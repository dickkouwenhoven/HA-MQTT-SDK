"""
Device Info Builder for Home Assistant MQTT SDK.

Purpose:
- Build standardized Home Assistant device info blocks
- Validate input data
- Map source device data to HA-compatible structure

This module is INTERNAL and should not be used directly by SDK users.

Used by:
- ha_mqtt_sdk.models.entity.make_entity
"""
from __future__ import annotations

from typing import Any
from collections.abc import Mapping

from ..utils.logger import get_logger
from ..exceptions import DeviceError

LOGGER = get_logger(__name__)

class DeviceInfo:
	"""
	Stateless Home Assistant device_info builder.
	"""

	# Default mapping from source device data → HA device info
	_DEFAULT_MAPPING: dict[str, str] = {
		"identifiers": "serial_number",
		"manufacturer": "manufacturer",
		"model": "model",
		"name": "name",
		"sw_version": "firmware_version",
		"hw_version": "hardware_version",
		"suggested_area": "room",
	}

	@staticmethod
	def _extract_value(
		source: Mapping[str, Any],
		path: str,
	) -> Any:
		"""
		Extract value using dot notation.
		
		Example: "attributes.serial_number"
		"""
		current: Any = source

		for key in path.split("."):
			if not isinstance(current, Mapping):
				return None

			current = current.get(key)

			if current is None:
				return None

		return current
		
	@staticmethod
	def _validate_device_input(
		device: Mapping[str, Any],
	) -> None:
		"""
		Validate raw device input.
		"""
		if not isinstance(device, Mapping):
			raise DeviceError("device must be a mapping")

		if not device:
			raise DeviceError("device cannot be empty")

	@staticmethod
	def _normalize_identifiers(
		value: Any,
	) -> list[tuple[str, str]]:
		"""
		Normalize identifiers to Home Assistant format.

		HA expects:
			[(domain, identifier)}
		"""

		if isinstance(value, str):
			if not value.strip():
				raise DeviceError("identifier cannot be empty")
			return [("ha_mqtt_sdk", value)]

		if isinstance(value, tuple):
			if len(value) != 2:
				raise DeviceError("identifier tuple must contain 2 items")

			return [value]

		if isinstance(value, list):
			normalized: list[tuple[str, str]] = []

			for item in value:
				if (
					not isinstance(item, tuple)
					or len(item) != 2
				):
					raise DeviceError("all identifiers must be 2-item tuples")

				normalized.append(item)

			return normalized

		raise DeviceError("identifiers must be a string, tuple, or list of tuples")

	
	@classmethod			
	def build_device_info(
		cls,
		device: Mapping[str, Any],
		mapping: Mapping[str, str] | None = None
	) -> dict[str, Any]:
		"""
		Build Home Assistant compatible device_info.

		Used by:
		ha_mqtt_sdk.models.entity.make_entity
		"""
		cls._validate_device_input(device)

		active_mapping = mapping or cls._DEFAULT_MAPPING
		
		device_info: dict[str, Any] = {}

		for ha_key, source_path in active_mapping.items():
			value = cls._extract_value(device, source_path,)
			
			if value is not None:
				device_info[ha_key] = value

		# Required HA field: identifiers must exist
		if "identifiers" not in device_info:
			raise DeviceError("Device info must contain 'identifiers'")

		# HA expects identifiers as list of tuples
		device_info["identifiers"] = (
			cls._normalize_identifiers(
				device_info["identifiers"]
			)
		)
		
		LOGGER.debug(
			"Built device_info with %d fields",
			len(device_info),
		)

		return device_info
