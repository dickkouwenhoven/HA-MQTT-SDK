from typing import Any

# Payload types accepted by the MQTT transport layer
PublishPayload = str | dict[str, Any] | int | float

# Valid state values for Home Assistant entities
# - bool excluded, use "ON"/"OFF" strings instead
StateValue = str | int | float
