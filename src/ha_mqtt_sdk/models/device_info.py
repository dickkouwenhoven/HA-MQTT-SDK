from typing import TypedDict


class DeviceInfo(TypedDict, total=False):
    identifiers: list[tuple[str, str]]

    manufacturer: str
    model: str
    name: str

    sw_version: str
    hw_version: str

    suggested_area: str

    connections: list[tuple[str, str]]
    via_device: tuple[str, str]
    configuration_url: str
    serial_number: str
    model_id: str
