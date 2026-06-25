"""
types.py

Shared type aliases used across the SDK.

Importing:
    from ha_mqtt_sdk.types import PublishPayload, StateValue
"""

from typing import Any

# Payload types accepted by the MQTT transport layer
type PublishPayload = str | dict[str, Any] | int | float

# Valid state values for Home Assistant entities
# - bool excluded, use "ON"/"OFF" strings instead
type StateValue = str | int | float
