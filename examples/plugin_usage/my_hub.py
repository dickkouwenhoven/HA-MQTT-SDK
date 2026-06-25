"""
my_hub.py

Simulated smart home hub for the plugin usage example.

In a real integration this would be replaced by the actual hub SDK,
for example:
- dirigera (IKEA Dirigera)
- phue (Philips Hue)
- python-zwave (Z-Wave)

This stub simulates:
- Device discovery
- State polling
- Command forwarding
"""

from collections.abc import Callable


class MyHubDevice:
    """Represents a single device on the hub."""

    def __init__(self, device_id: str, name: str, device_type: str, state: str) -> None:
        self.device_id = device_id
        self.name = name
        self.device_type = device_type
        self.state = state


class MyHub:
    """
    Simulated hub client.

    Replace this with your actual hub SDK in a real integration.
    """

    def __init__(self, host: str) -> None:
        self._host = host
        self._on_state_change: Callable[[str, str], None] | None = None

        # Simulated devices returned by the hub
        self._devices = [
            MyHubDevice("bulb_001", "Living Room Bulb", "light", "OFF"),
            MyHubDevice("bulb_002", "Kitchen Bulb", "light", "ON"),
            MyHubDevice("sensor_001", "Hallway Temperature", "sensor", "19.5"),
        ]

    def get_devices(self) -> list[MyHubDevice]:
        """Return all devices known to the hub."""
        return self._devices

    def set_state(self, device_id: str, state: str) -> None:
        """
        Send a command to a device.

        In a real hub this would be an HTTP/WebSocket call.
        """
        print(f"[HUB] Sending command to {device_id}: {state}")

        for device in self._devices:
            if device.device_id == device_id:
                device.state = state

                # Notify listener of the state change
                if self._on_state_change:
                    self._on_state_change(device_id, state)

    def on_state_change(self, callback: Callable[[str, str], None]) -> None:
        """Register a callback for device state changes."""
        self._on_state_change = callback
