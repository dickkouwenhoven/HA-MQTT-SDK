"""
Async plugin usage example showing how to build a production integration
using AsyncIntegrationPlugin (async path).

This example simulates a WebSocket-based smart hub integration to demonstrate
the full async plugin lifecycle:

    1. setup()          — connect to hub, discover devices, register entities
    2. start()          — launch asyncio task to listen for hub events
    3. handle_command() — handle commands from Home Assistant
    4. stop()           — cancel task, disconnect hub

For the sync equivalent, see examples/plugin_usage/.
"""

import asyncio

from ha_mqtt_sdk import HADomain, MQTTSettings
from ha_mqtt_sdk.core.async_sdk import AsyncHASDK
from ha_mqtt_sdk.mqtt.async_client import AsyncMQTTClient

from .my_async_hub import MyAsyncHub
from .my_async_hub_plugin import MyAsyncHubPlugin


async def main() -> None:
    # ── 1. Configure and initialize the SDK ───────────────────────────────────

    mqtt_config = MQTTSettings(
        host="localhost",
        port=1883,
    )
    client = AsyncMQTTClient(config=mqtt_config)
    sdk = AsyncHASDK(async_mqtt_client=client)

    # ── 2. Create your async hub connection ───────────────────────────────────

    hub = MyAsyncHub(
        host="192.168.1.100",
        token="your-hub-token-here",
    )

    # ── 3. Register the plugin ────────────────────────────────────────────────

    sdk.use_plugin("my_async_hub", MyAsyncHubPlugin(hub))

    # ── 4. Run — connects MQTT, calls setup(), then start() on all plugins ────

    await sdk.run()

    # At this point the integration is live:
    # - Entities are registered in Home Assistant
    # - Hub events are consumed by the asyncio listener task
    # - State changes are pushed to HA via MQTT
    # - Commands from HA are forwarded to the hub

    # ── 5. Simulate a hub event (demo only) ───────────────────────────────────
    #
    # In production the hub pushes events automatically over WebSocket.
    # Here we inject one manually to demonstrate the flow.

    print("\n[main] Simulating a hub state change event...")
    await hub.simulate_event("bulb_001", "ON")

    # Give the listener task time to process the event
    await asyncio.sleep(0.1)

    # ── 6. Shutdown — calls stop() on all plugins, then disconnects MQTT ──────

    await sdk.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
