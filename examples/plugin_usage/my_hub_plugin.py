"""
my_hub_plugin.py

Concrete IntegrationPlugin implementation for MyHub.

This is the file you model your own integration after.

Responsibilities:
- Map hub devices to HA entities (setup)
- Start listening for hub state changes (start)
- Forward HA commands to the hub (handle_command)
- Clean up on shutdown (stop)
"""

import threading

from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.core.plugin_interface import IntegrationPlugin
from ha_mqtt_sdk.core.sdk import HASDK
from ha_mqtt_sdk.models.entity import Entity

from .my_hub import MyHub, MyHubDevice

# Map hub device types to Home Assistant domains
_DOMAIN_MAP: dict[str, HADomain] = {
    "light": HADomain.LIGHT,
    "sensor": HADomain.SENSOR,
}


class MyHubPlugin(IntegrationPlugin):
    """
    IntegrationPlugin implementation for MyHub.

    This plugin:
    - Discovers devices from MyHub on setup
    - Maps each device to a Home Assistant entity
    - Listens for state changes and pushes them to HA
    - Forwards HA commands back to the hub
    """

    def __init__(self, hub: MyHub) -> None:
        self._hub = hub
        self._sdk: HASDK | None = None

        # Maps hub device_id → registered Entity
        self._entities: dict[str, Entity] = {}

        self._running = False
        self._thread: threading.Thread | None = None

    # ── IntegrationPlugin interface ───────────────────────────────────────────

    def setup(self, sdk: HASDK) -> None:
        """
        Discover hub devices and register them as HA entities.

        Called once by PluginManager before start().
        """
        self._sdk = sdk

        print("[MyHubPlugin] Discovering devices...")

        for device in self._hub.get_devices():
            entity = self._map_device(device, sdk)

            if entity is None:
                print(f"[MyHubPlugin] Skipping unsupported device type: {device.device_type}")
                continue

            self._entities[device.device_id] = entity

            # Determine if this entity accepts commands
            command_callback = None
            if device.device_type == "light":
                command_callback = self.handle_command

            sdk.register(entity, command_callback=command_callback)

            print(f"[MyHubPlugin] Registered: {device.name} ({device.device_type})")

        # Register hub state change listener
        self._hub.on_state_change(self._on_hub_state_change)

    def start(self) -> None:
        """
        Start a background thread to simulate hub event polling.

        In a real integration this might open a WebSocket connection
        or start an event loop in a daemon thread.
        """
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print("[MyHubPlugin] Started listening for hub events")

    def stop(self) -> None:
        """
        Stop the background thread and clean up.

        Called by PluginManager during SDK shutdown.
        """
        self._running = False

        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

        print("[MyHubPlugin] Stopped")

    def handle_command(self, topic: str, payload: str) -> None:
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
            print(f"[MyHubPlugin] Unrecognised command topic: {topic}")
            return

        device_id = parts[-2]

        print(f"[MyHubPlugin] Command received for {device_id}: {payload}")

        self._hub.set_state(device_id, payload)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _map_device(self, device: MyHubDevice, sdk: HASDK) -> Entity | None:
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

    def _on_hub_state_change(self, device_id: str, state: str) -> None:
        """
        Called by the hub when a device changes state.

        Pushes the new state to Home Assistant via MQTT.
        """
        entity = self._entities.get(device_id)

        if entity is None:
            print(f"[MyHubPlugin] State change for unknown device: {device_id}")
            return

        if self._sdk is None:
            return

        self._sdk.update_state(entity, state)
        print(f"[MyHubPlugin] State pushed to HA: {device_id} -> {state}")

    def _poll_loop(self) -> None:
        """
        Background polling loop.

        In this example it does nothing — in a real integration
        this would poll the hub for state changes or process
        incoming WebSocket messages.
        """
        import time

        while self._running:
            time.sleep(1)
