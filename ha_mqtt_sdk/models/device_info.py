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

from typing import Dict, Any
from ..utils.logger import get_logger
from ..exceptions import DeviceError

LOGGER = get_logger(__name__)


# Default mapping from source device data → HA device info
_DEFAULT_MAPPING = {
	"identifiers": "serial_number",
	"manufacturer": "manufacturer",
	"model": "model",
	"name": "name",
	"sw_version": "firmware_version",
	"hw_version": "hardware_version",
	"suggested_area": "room",
}


def _extract_value(source: Dict[str, Any], path: str) -> Any:
	"""
	Extract value from dict using dot-notation path.
	Example: "attributes.serialNumber"
	"""
	try:
		keys = path.split(".")
		value = source
		for key in keys:
			value = value[key]
		return value
	except (KeyError, TypeError):
		return None


def _validate_device_input(device: Dict[str, Any]) -> None:
	"""
	Validate input device data.
	"""
	if not isinstance(device, dict):
		raise DeviceError("device must be a dictionary")

	if not device:
		raise DeviceError("device cannot be empty")


def build_device_info(
	device: Dict[str, Any],
	mapping: Dict[str, str] = None
) -> Dict[str, Any]:
	"""
	Build Home Assistant device info structure.

	Args:
	device: Source device data (raw input)
	mapping: Optional custom mapping

	Returns:
	Dict[str, Any]: HA device info block

	Used by:
	sdk.models.entity.make_entity
	"""
	_validate_device_input(device)

	mapping = mapping or _DEFAULT_MAPPING
	device_info: Dict[str, Any] = {}

	for ha_key, source_path in mapping.items():
		value = _extract_value(device, source_path)
		if value is not None:
			device_info[ha_key] = value

	# Required HA field: identifiers must exist
	if "identifiers" not in device_info:
		raise DeviceError("Device info must contain 'identifiers'")

	# HA expects identifiers as list of tuples
	if not isinstance(device_info["identifiers"], list):
		device_info["identifiers"] = [(device_info["identifiers"],)]

	LOGGER.debug("Built device_info: %s", device_info)

	return device_info
