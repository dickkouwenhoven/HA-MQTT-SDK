from typing import TypedDict

class DeviceInfo(TypedDict, total=False):
    identifiers: list[tuple[str, str]] | None = None
    
    manufacturer: str | None = None
    model: str | None = None
    name: str | None = None
    
    sw_version: str | None = None
    hw_version: str | None = None
    
    suggested_area: str | None = None

    connections: set[tuple[str, str]] | None = None
    via_device: tuple[str, str] | None = None
    configuration_url: str | None = None
    serial_number: str | None = None
    model_id: str | None = None
