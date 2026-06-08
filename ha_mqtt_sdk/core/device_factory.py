"""
DeviceInfo factory helpers.

Provides:
- Type-safe creation of DeviceInfo structures
"""

from ..models.device_info import DeviceInfo


def create_device_info(
    *,
    identifiers: set[tuple[str, str]] | None = None,
    connections: set[tuple[str, str]] | None = None,
    manufacturer: str | None = None,
    model: str | None = None,
    name: str | None = None,
    sw_version: str | None = None,
    hw_version: str | None = None,
    suggested_area: str | None = None,
    via_device: tuple[str, str] | None = None,
    configuration_url: str | None = None,
    serial_number: str | None = None,
    model_id: str | None = None,
) -> DeviceInfo:
    """
    Create a Home Assistant DeviceInfo object.
    """

    device_info: DeviceInfo = {}

    if identifiers is not None:
        device_info["identifiers"] = identifiers

    if connections is not None:
        device_info["connections"] = connections

    if manufacturer is not None:
        device_info["manufacturer"] = manufacturer

    if model is not None:
        device_info["model"] = model

    if name is not None:
        device_info["name"] = name

    if sw_version is not None:
        device_info["sw_version"] = sw_version

    if hw_version is not None:
        device_info["hw_version"] = hw_version

    if suggested_area is not None:
        device_info["suggested_area"] = suggested_area

    if via_device is not None:
        device_info["via_device"] = via_device

    if configuration_url is not None:
        device_info["configuration_url"] = configuration_url

    if serial_number is not None:
        device_info["serial_number"] = serial_number

    if model_id is not None:
        device_info["model_id"] = model_id

    return device_info
