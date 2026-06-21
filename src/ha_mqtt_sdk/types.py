from typing import Any

# Payload types accepted by the MQTT transport layer
PublishPayload = str | dict[str, Any] | int | float

# Valid state values for Home Assistant entities
StateValue = str | int | float | bool
