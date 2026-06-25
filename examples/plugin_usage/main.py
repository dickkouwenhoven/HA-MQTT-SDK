"""
Plugin usage example showing how to build a production integration
using IntegrationPlugin (sync path).

This example simulates a simple smart bulb integration to demonstrate
the full plugin lifecycle:

    1. setup()         — discover devices, register entities
    2. start()         — start listening for device state changes
    3. handle_command() — handle commands from Home Assistant
    4. stop()          — clean up on shutdown

For the async equivalent, see examples/async_plugin_usage/.
"""

from ha_mqtt_sdk import MQTTSettings, PahoMQTTClient
from ha_mqtt_sdk.core.sdk import HASDK

from .my_hub import MyHub
from .my_hub_plugin import MyHubPlugin


def main() -> None:
    # ── 1. Configure and initialize the SDK ───────────────────────────────────

    mqtt_config = MQTTSettings(
        host="localhost",
        port=1883,
    )
    client = PahoMQTTClient(config=mqtt_config)
    sdk = HASDK(mqtt_client=client)

    # ── 2. Create your hub connection ─────────────────────────────────────────

    hub = MyHub(host="192.168.1.100")

    # ── 3. Register the plugin ────────────────────────────────────────────────

    sdk.use_plugin("my_hub", MyHubPlugin(hub))

    # ── 4. Run — connects MQTT, calls setup(), then start() on all plugins ────

    sdk.run()

    # At this point the integration is live:
    # - Entities are registered in Home Assistant
    # - State changes from the hub are published to MQTT
    # - Commands from HA are forwarded to the hub

    # ── 5. Shutdown — calls stop() on all plugins, then disconnects MQTT ──────

    sdk.shutdown()


if __name__ == "__main__":
    main()
