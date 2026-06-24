"""
async_plugin_interface.py

Abstract base class for asynchronous hub integrations.

Every async integration must subclass AsyncIntegrationPlugin
and implement all abstract methods.

Lifecycle (managed by AsyncPluginManager via AsyncHASDK.run()):
    1. plugin.setup(sdk)       — discover devices, create and register entities
    2. plugin.start()          — connect to hub, launch asyncio task
    3. hub state change        — plugin calls sdk.update_state()
    4. HA command arrives      — plugin.handle_command() is called
    5. plugin.stop()           — cancel tasks, close connections

Used by:
- ha_mqtt_sdk/core/async_plugin_manager.py
- End users building async integrations (e.g. Dirigera bridge)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .async_sdk import AsyncHASDK


class AsyncIntegrationPlugin(ABC):
    """
    Base class for asynchronous hub integrations.

    Subclass this to integrate a new hub with Home Assistant
    via the HA-MQTT-SDK async path.

    Example::

        class DirigeraPlugin(AsyncIntegrationPlugin):
            async def setup(self, sdk: AsyncHASDK) -> None:
                devices = await self._fetch_devices()
                for device in devices:
                    entity = sdk.create_entity(
                        domain=map_domain(device),
                        name=device["name"],
                        unique_id=device["id"],
                    )
                    await sdk.register(entity, command_callback=self.handle_command)

            async def start(self) -> None:
                self._task = asyncio.create_task(self._listen_websocket())

            async def stop(self) -> None:
                if self._task:
                    self._task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await self._task

            async def handle_command(self, topic: str, payload: str) -> None:
                # translate and forward to Dirigera hub
                ...
    """

    @abstractmethod
    async def setup(self, sdk: AsyncHASDK) -> None:
        """
        Called once on startup before start().

        Responsibilities:
        - Discover devices from the hub
        - Create entities via sdk.create_entity()
        - Register entities via await sdk.register()

        Args:
            sdk: The AsyncHASDK instance to register entities with
        """

    @abstractmethod
    async def start(self) -> None:
        """
        Start listening for state changes from the hub.

        Called after setup() completes. Implementations typically
        launch an asyncio Task here (websocket listener, poller, etc.)

        On state change: call await sdk.update_state() to push to HA.
        """

    @abstractmethod
    async def stop(self) -> None:
        """
        Disconnect from the hub and clean up all resources.

        Called on shutdown. Must not raise — catch and suppress
        CancelledError and other errors internally.
        """

    @abstractmethod
    async def handle_command(self, topic: str, payload: str) -> None:
        """
        Handle an incoming command from Home Assistant.

        Called by the SDK when HA publishes to a command topic.
        Implementations must translate the command and forward
        it to the hub.

        Args:
            topic:   The MQTT command topic (e.g. "homeassistant/switch/my_id/set")
            payload: The command payload (e.g. "ON", "OFF", "50")
        """
