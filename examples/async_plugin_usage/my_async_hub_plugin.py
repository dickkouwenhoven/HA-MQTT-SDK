"""
my_async_hub_plugin.py

Concrete AsyncIntegrationPlugin implementation for MyAsyncHub.

This is the file you model your own async integration after.

Responsibilities:
- Map hub devices to HA entities (setup)
- Start an asyncio task to listen for hub events (start)
- Forward HA commands to the hub (handle_command)
- Cancel the task and disconnect cleanly (stop)
"""

import asyncio
import contextlib

from .my_async_hub import MyAsyncHub, MyAsyncHubDevice

from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.core.async_plugin_interface import AsyncIntegrationPlugin
from ha_mqtt_sdk.core.async_sdk import AsyncHASDK
from ha_mqtt_sdk.models.entity import Entity


# Map hub device types to Home Assistant domains
_DOMAIN_MAP: dict[str, HADomain] = {
    "light": HADomain.LIGHT,
    "sensor": HADomain.SENSOR,
}


class MyAsyncHubPlugin(AsyncIntegrationPlugin):
    """
    AsyncIntegrationPlugin implementation for MyAsyncHub.

    This plugin:
    - Discovers devices from MyAsyncHub on setup
    - Maps each device to a Home Assistant entity
    - Listens for hub events via an asyncio Task and pushes them to HA
    - Forwards HA commands back to the hub
    """

    def __init__(self, hub: MyAsyncHub) -> None:
        self._hub = hub
        self._sdk: AsyncHASDK | None = None

        # Maps hub device_id → registered Entity
        self._entities: dict[str, Entity] = {}

        self._listen_task: asyncio.Task | None = None

    # ── AsyncIntegrationPlugin interface ──────────────────────────────────────

    async def setup(self, sdk: AsyncHASDK) -> None:
        """
        Connect to the hub, discover devices and register them as HA entities.

        Called once by AsyncPluginManager before start().
        """
        self._sdk = sdk

        await self._hub.connect()

        print("[MyAsyncHubPlugin] Discovering devices...")

        for device in await self._hub.get_devices():
            entity = self._map_device(device, sdk)

            if entity is None:
                print(
                    f"[MyAsyncHubPlugin] Skipping unsupported device type: {device.device_type}"
                )
                continue

            self._entities[device.device_id] = entity

            # Determine if this entity accepts commands
            command_callback = None
            if device.device_type == "light":
                command_callback = self.handle_command

            await sdk.register(entity, command_callback=command_callback)

            print(f"[MyAsyncHubPlugin] Registered: {device.name} ({device.device_type})")

    async def start(self) -> None:
        """
        Launch an asyncio Task to listen for hub state change events.

        The task runs concurrently with the rest of the application.
        In a real integration this would consume a WebSocket stream.
        """
        self._listen_task = asyncio.create_task(
            self._listen_for_events(),
            name="my_async_hub_listener",
        )
        print("[MyAsyncHubPlugin] Listener task started")

    async def stop(self) -> None:
        """
        Cancel the listener task and disconnect from the hub.

        Called by AsyncPluginManager during SDK shutdown.
        CancelledError is suppressed — stop() must never raise.
        """
        if self._listen_task:
            self._listen_task.cancel()

            with contextlib.suppress(asyncio.CancelledError):
                await self._listen_task

            self._listen_task = None

        await self._hub.disconnect()
        print("[MyAsyncHubPlugin] Stopped")

    async def handle_command(self, topic: str, payload: str) -> None:
        """
        Forward an HA command to the hub.

        Called when Home Assistant publishes to a command topic,
        for example when a user toggles a light in the dashboard.

        Args:
            topic:   e.g. "homeassistant/light/bulb_001/set"
            payload: e.g. "ON" or "OFF"
        """
        # Extract device_id from topic: homeassistant/<domain>/<device_id>/set
        parts = topic.split("/")
        if len(parts) < 3:
            print(f"[MyAsyncHubPlugin] Unrecognised command topic: {topic}")
            return

        device_id = parts[-2]

        print(f"[MyAsyncHubPlugin] Command received for {device_id}: {payload}")

        await self._hub.set_state(device_id, payload)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _map_device(self, device: MyAsyncHubDevice, sdk: AsyncHASDK) -> Entity | None:
        """
        Map a hub device to an HA Entity.

        Returns None if the device type is not supported.
        """
        domain = _DOMAIN_MAP.get(device.device_type)

        if domain is None:
            return None

        return sdk.create_entity(
            domain=domain,
            name=device.name,
            unique_id=device.device_id,
        )

    async def _listen_for_events(self) -> None:
        """
        Consume the hub event stream and push state changes to HA.

        Runs as a long-lived asyncio Task. Exits cleanly on CancelledError.
        """
        print("[MyAsyncHubPlugin] Listening for hub events...")

        try:
            async for device_id, state in self._hub.events():
                await self._on_hub_event(device_id, state)
        except asyncio.CancelledError:
            print("[MyAsyncHubPlugin] Listener task cancelled")
            raise
        except Exception as e:
            print(f"[MyAsyncHubPlugin] Listener error: {e}")

    async def _on_hub_event(self, device_id: str, state: str) -> None:
        """
        Handle a single hub state change event.

        Pushes the new state to Home Assistant via MQTT.
        """
        entity = self._entities.get(device_id)

        if entity is None:
            print(f"[MyAsyncHubPlugin] Event for unknown device: {device_id}")
            return

        if self._sdk is None:
            return

        await self._sdk.update_state(entity, state)
        print(f"[MyAsyncHubPlugin] State pushed to HA: {device_id} -> {state}")
