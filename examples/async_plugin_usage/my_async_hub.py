"""
my_async_hub.py

Simulated async smart home hub for the async_plugin_usage example.

In a real integration this would be replaced by the actual hub SDK,
for example:
- dirigera (IKEA Dirigera) — WebSocket based
- aiohue (Philips Hue) — async HTTP + SSE
- python-zwave (Z-Wave) — event driven

This stub simulates:
- Async device discovery
- WebSocket-style event streaming
- Async command forwarding
"""

import asyncio
from collections.abc import AsyncIterator


class MyAsyncHubDevice:
    """Represents a single device on the async hub."""

    def __init__(
        self,
        device_id: str,
        name: str,
        device_type: str,
        state: str,
    ) -> None:
        self.device_id = device_id
        self.name = name
        self.device_type = device_type
        self.state = state


class MyAsyncHub:
    """
    Simulated async hub client.

    Replace this with your actual hub SDK in a real integration.
    All I/O methods are async to reflect real-world hub SDKs that
    use aiohttp, WebSockets, or similar.
    """

    def __init__(self, host: str, token: str) -> None:
        self._host = host
        self._token = token
        self._running = False

        # Simulated devices returned by the hub
        self._devices = [
            MyAsyncHubDevice("bulb_001", "Living Room Bulb", "light", "OFF"),
            MyAsyncHubDevice("bulb_002", "Kitchen Bulb", "light", "ON"),
            MyAsyncHubDevice("sensor_001", "Hallway Temperature", "sensor", "19.5"),
        ]

        # Queue used to simulate incoming hub events
        self._event_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()

    async def connect(self) -> None:
        """Connect to the hub (open WebSocket, authenticate, etc.)."""
        print(f"[MyAsyncHub] Connecting to {self._host}...")
        await asyncio.sleep(0)  # simulate I/O
        self._running = True
        print("[MyAsyncHub] Connected")

    async def disconnect(self) -> None:
        """Disconnect from the hub."""
        self._running = False
        print("[MyAsyncHub] Disconnected")

    async def get_devices(self) -> list[MyAsyncHubDevice]:
        """Return all devices known to the hub."""
        await asyncio.sleep(0)  # simulate network call
        return list(self._devices)

    async def set_state(self, device_id: str, state: str) -> None:
        """
        Send a command to a device.

        In a real hub this would be an async HTTP call or WebSocket message.
        """
        print(f"[MyAsyncHub] Sending command to {device_id}: {state}")

        for device in self._devices:
            if device.device_id == device_id:
                device.state = state
                # Simulate the hub echoing back the state change as an event
                await self._event_queue.put((device_id, state))

        await asyncio.sleep(0)  # simulate network latency

    async def events(self) -> AsyncIterator[tuple[str, str]]:
        """
        Async generator that yields (device_id, state) tuples.

        In a real hub this would be a WebSocket message stream or
        a Server-Sent Events iterator. This stub yields from an
        internal queue so tests and examples can inject events.
        """
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0,
                )
                yield event
            except TimeoutError:
                continue

    async def simulate_event(self, device_id: str, state: str) -> None:
        """
        Inject a simulated hub event (for testing / demo purposes).

        In production this is not needed — real hubs push events automatically.
        """
        await self._event_queue.put((device_id, state))
