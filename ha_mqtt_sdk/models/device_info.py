from typing import TypedDict


class DeviceInfo(TypedDict, total=False):
    identifiers: list[tuple[str, str]] | None

    manufacturer: str | None
    model: str | None
    name: str | None

    sw_version: str | None
    hw_version: str | None

    suggested_area: str | None

    connections: list[tuple[str, str]] | None
    via_device: tuple[str, str] | None
    configuration_url: str | None
    serial_number: str | None
    model_id: str | None
