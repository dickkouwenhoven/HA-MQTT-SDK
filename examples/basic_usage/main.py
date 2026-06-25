"""
Basic example showing how to use the HASDK (sync path).

This example demonstrates the simple synchronous API — the recommended
starting point for new integrations.

For production integrations, see examples/plugin_usage/ which shows
how to structure a full integration using IntegrationPlugin.
"""

from ha_mqtt_sdk import (
    HASDK,
    HADomain,
    MQTTSettings,
    PahoMQTTClient,
)


def on_light_command(topic: str, payload: str) -> None:
    """
    Called when Home Assistant sends a command to the light.

    For example: when the user toggles the light in the HA dashboard.
    """
    print(f"[COMMAND] {topic} -> {payload}")

    # Here you would forward the command to your actual device
    # e.g. hue_bridge.set_light("demo_lamp", payload)


def main() -> None:
    # ── 1. Configure MQTT connection ──────────────────────────────────────────

    mqtt_config = MQTTSettings(
        host="localhost",
        port=1883,
    )
    client = PahoMQTTClient(config=mqtt_config)

    # ── 2. Initialize the SDK ─────────────────────────────────────────────────

    sdk = HASDK(mqtt_client=client)

    # ── 3. Create entities ────────────────────────────────────────────────────

    # Use sdk.create_entity() — this validates the entity against the HA schema
    light = sdk.create_entity(
        domain=HADomain.LIGHT,
        name="Demo Lamp",
        unique_id="demo_lamp_1",
    )

    sensor = sdk.create_entity(
        domain=HADomain.SENSOR,
        name="Demo Temperature",
        unique_id="demo_temp_1",
        extra={"unit_of_measurement": "°C", "device_class": "temperature"},
    )

    # ── 4. Connect to MQTT broker ─────────────────────────────────────────────

    sdk.start()

    # ── 5. Register entities in Home Assistant ────────────────────────────────

    # Light supports commands (on/off) — provide a callback
    sdk.register(light, command_callback=on_light_command)

    # Sensor is read-only — no command callback needed
    sdk.register(sensor)

    # ── 6. Publish state and availability ─────────────────────────────────────

    sdk.update_state(light, "ON")
    sdk.update_state(sensor, 21.5)

    # ── 7. Shutdown ───────────────────────────────────────────────────────────

    sdk.shutdown()


if __name__ == "__main__":
    main()
