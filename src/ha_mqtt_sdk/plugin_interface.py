"""
plugin_interface.py

Abstract base class for synchronous hub integrations.

Every sync integration (Dirigera, Philips Hue, Z-Wave, etc.) must subclass
IntegrationPlugin and implement all abstract methods.

Lifecycle (managed by PluginManager via HASDK.run()):
    1. plugin.setup(sdk)       — discover devices, create and register entities
    2. plugin.start()          — connect to hub, start background thread
    3. hub state change        — plugin calls sdk.update_state()
    4. HA command arrives      — plugin.handle_command() is called
    5. plugin.stop()           — disconnect from hub, clean up thread

Used by:
- ha_mqtt_sdk/core/plugin_manager.py
- End users building sync integrations
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sdk import HASDK


class IntegrationPlugin(ABC):
    """
    Base class for synchronous hub integrations.

    Subclass this to integrate a new hub (Hue, Z-Wave, etc.)
    with Home Assistant via the HA-MQTT-SDK sync path.

    Example::

        class MyHuePlugin(IntegrationPlugin):
            def setup(self, sdk: HASDK) -> None:
                entity = sdk.create_entity(
                    domain=HADomain.LIGHT,
                    name="Hallway Bulb",
                    unique_id="hue_bulb_1",
                )
                sdk.register(entity, command_callback=self.handle_command)

            def start(self) -> None:
                self._thread = threading.Thread(target=self._poll_loop, daemon=True)
                self._thread.start()

            def stop(self) -> None:
                self._running = False
                self._thread.join(timeout=5)

            def handle_command(self, topic: str, payload: str) -> None:
                # translate payload and forward to Hue bridge
                ...
    """

    @abstractmethod
    def setup(self, sdk: HASDK) -> None:
        """
        Called once on startup before start().

        Responsibilities:
        - Discover devices from the hub
        - Create entities via sdk.create_entity()
        - Register entities via sdk.register()

        Args:
            sdk: The HASDK instance to register entities with
        """

    @abstractmethod
    def start(self) -> None:
        """
        Start listening for state changes from the hub.

        Called after setup() completes. Implementations typically
        start a background daemon thread here.

        On state change: call sdk.update_state() to push to HA.
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Disconnect from the hub and clean up all resources.

        Called on shutdown. Must not raise — errors should be
        caught and logged internally.
        """

    @abstractmethod
    def handle_command(self, topic: str, payload: str) -> None:
        """
        Handle an incoming command from Home Assistant.

        Called by the SDK when HA publishes to a command topic.
        Implementations must translate the command and forward
        it to the hub.

        Args:
            topic:   The MQTT command topic (e.g. "homeassistant/switch/my_id/set")
            payload: The command payload (e.g. "ON", "OFF", "50")
        """
