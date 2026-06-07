from typing import TypedDict

class DeviceInfo(TypedDict, total=False):
    identifiers: list[tuple[str, str]]
    
    manufacturer: str
    model: str
    name: str
    
    sw_version: str
    hw_version: str
    
    suggested_area: str
