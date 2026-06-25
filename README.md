# Home Assistant MQTT SDK

Production-ready Python SDK for integrating devices and applications with Home Assistant through MQTT Discovery.

The SDK simplifies Home Assistant MQTT integration by automatically handling:

- MQTT Discovery payload generation
- MQTT topic management
- Entity registration and validation
- State and availability updates
- Command handling
- Plugin system for structured integrations
- Sync and Async paths

---

## Features

- Home Assistant MQTT Discovery support
- Automatic MQTT topic generation
- Entity schema validation
- Availability management
- Command callback handling
- Plugin system (`IntegrationPlugin` / `AsyncIntegrationPlugin`)
- Sync MQTT support via Paho MQTT
- Async MQTT support via aiomqtt
- Dependency injection support
- Extensive test coverage (100%)
- Type-checked with mypy
- Docker support

---

## Requirements

- Python 3.12+
- MQTT Broker (Mosquitto recommended)
- Home Assistant with MQTT integration enabled

---

## Installation

Install from PyPI:

```bash
pip install ha_mqtt_sdk
```

Or install from source:

```bash
git clone https://github.com/dickkouwenhoven/HA-MQTT-SDK.git
cd HA-MQTT-SDK
pip install -e .
```

---

## Two Paths

The SDK provides two parallel APIs:

| | Sync | Async |
|---|---|---|
| **Entry point** | `HASDK` | `AsyncHASDK` |
| **Manager** | `EntityManager` | `AsyncEntityManager` |
| **MQTT client** | `PahoMQTTClient` | `AsyncMQTTClient` |
| **Plugin base** | `IntegrationPlugin` | `AsyncIntegrationPlugin` |
| **Use when** | Simple integrations | Concurrent / WebSocket integrations |

---

## Quick Start (Sync)

```python
from ha_mqtt_sdk import HADomain, MQTTSettings, PahoMQTTClient
from ha_mqtt_sdk.core.sdk import HASDK

# 1. Configure connection
mqtt_config = MQTTSettings(host="localhost", port=1883)
client = PahoMQTTClient(config=mqtt_config)
sdk = HASDK(mqtt_client=client)

# 2. Create entities — validated against the HA schema
sensor = sdk.create_entity(
    domain=HADomain.SENSOR,
    name="Temperature",
    unique_id="temp_1",
    extra={"unit_of_measurement": "°C", "device_class": "temperature"},
)

light = sdk.create_entity(
    domain=HADomain.LIGHT,
    name="Living Room",
    unique_id="light_1",
)

# 3. Connect and register
sdk.start()

sdk.register(sensor)                                    # read-only, no callback
sdk.register(light, command_callback=handle_command)    # accepts HA commands

# 4. Publish state
sdk.update_state(sensor, 21.5)
sdk.update_state(light, "ON")

# 5. Shutdown
sdk.shutdown()
```

### Handling commands

```python
def handle_command(topic: str, payload: str) -> None:
    print(f"Command received: {topic} -> {payload}")
    # forward to your device here
```

---

## Quick Start (Async)

```python
import asyncio
from ha_mqtt_sdk import HADomain, MQTTSettings
from ha_mqtt_sdk.mqtt.async_client import AsyncMQTTClient
from ha_mqtt_sdk.core.async_sdk import AsyncHASDK

async def main() -> None:
    mqtt_config = MQTTSettings(host="localhost", port=1883)
    client = AsyncMQTTClient(config=mqtt_config)
    sdk = AsyncHASDK(async_mqtt_client=client)

    sensor = sdk.create_entity(
        domain=HADomain.SENSOR,
        name="Temperature",
        unique_id="temp_1",
    )

    await sdk.start()
    await sdk.register(sensor)
    await sdk.update_state(sensor, 21.5)
    await sdk.shutdown()

asyncio.run(main())
```

---

## Device Info

Attach device information to group entities under one device in Home Assistant:

```python
from ha_mqtt_sdk.models.device_info import DeviceInfo

device_info: DeviceInfo = {
    "identifiers": [("my_integration", "device_ABC123")],
    "manufacturer": "IKEA",
    "model": "DIRIGERA",
    "name": "My Hub",
}

entity = sdk.create_entity(
    domain=HADomain.SENSOR,
    name="Temperature",
    unique_id="temp_1",
    device_info=device_info,
)
```

---

## Plugin System

For production integrations the SDK provides a plugin system that manages
the full device lifecycle. Use this when building integrations for real hubs
(Dirigera, Philips Hue, Z-Wave, etc.).

### Sync plugin

```python
from ha_mqtt_sdk.core.plugin_interface import IntegrationPlugin
from ha_mqtt_sdk.core.sdk import HASDK

class MyHubPlugin(IntegrationPlugin):

    def setup(self, sdk: HASDK) -> None:
        """Discover devices and register entities."""
        for device in self._hub.get_devices():
            entity = sdk.create_entity(
                domain=HADomain.LIGHT,
                name=device.name,
                unique_id=device.id,
            )
            sdk.register(entity, command_callback=self.handle_command)

    def start(self) -> None:
        """Start listening for hub state changes (e.g. background thread)."""
        ...

    def stop(self) -> None:
        """Disconnect and clean up."""
        ...

    def handle_command(self, topic: str, payload: str) -> None:
        """Forward HA commands to the hub."""
        ...

# Wire up and run
sdk = HASDK(mqtt_client=client)
sdk.use_plugin("my_hub", MyHubPlugin(hub))
sdk.run()       # connect → setup → start
sdk.shutdown()  # stop → disconnect
```

### Async plugin

```python
from ha_mqtt_sdk.core.async_plugin_interface import AsyncIntegrationPlugin
from ha_mqtt_sdk.core.async_sdk import AsyncHASDK

class DirigeraPlugin(AsyncIntegrationPlugin):

    async def setup(self, sdk: AsyncHASDK) -> None:
        devices = await self._hub.get_devices()
        for device in devices:
            entity = sdk.create_entity(
                domain=HADomain.LIGHT,
                name=device.name,
                unique_id=device.id,
            )
            await sdk.register(entity, command_callback=self.handle_command)

    async def start(self) -> None:
        self._task = asyncio.create_task(self._listen())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()

    async def handle_command(self, topic: str, payload: str) -> None:
        await self._hub.send_command(topic, payload)

# Wire up and run
sdk = AsyncHASDK(async_mqtt_client=client)
sdk.use_plugin("dirigera", DirigeraPlugin(hub))
await sdk.run()       # connect → setup → start
await sdk.shutdown()  # stop → disconnect
```

See `examples/plugin_usage/` for a fully worked sync example and
`examples/async_plugin_usage/` for the async equivalent.

---

## Supported Entity Domains

```python
from ha_mqtt_sdk import HADomain

HADomain.SENSOR
HADomain.SWITCH
HADomain.LIGHT
HADomain.BINARY_SENSOR
HADomain.CLIMATE
# ... and more
```

The complete list is in `ha_mqtt_sdk/config/domains.py`.

---

## Architecture

```
Your Application
      │
      ▼
 HASDK / AsyncHASDK          ← public entry point
      │
      ├── PluginManager      ← optional: manages plugin lifecycle
      │       └── IntegrationPlugin (your integration code)
      │
      ├── EntityManager      ← entity lifecycle, topic routing
      │
      └── MQTT Client        ← Paho (sync) or aiomqtt (async)
              │
              ▼
        MQTT Broker
              │
              ▼
       Home Assistant
```

---

## Project Structure

```
HA-MQTT-SDK/
├── examples/
│   ├── basic_usage/              ← simple sync example
│   └── plugin_usage/             ← full plugin-based integration example
├── src/
│   └── ha_mqtt_sdk/
│       ├── builders/             ← topic + payload builders
│       ├── config/               ← domains, MQTT settings, field schemas
│       ├── core/                 ← SDK, managers, factory, plugin system
│       │   ├── sdk.py
│       │   ├── async_sdk.py
│       │   ├── entity_manager.py
│       │   ├── async_entity_manager.py
│       │   ├── entity_factory.py
│       │   ├── plugin_interface.py
│       │   ├── async_plugin_interface.py
│       │   ├── plugin_manager.py
│       │   └── async_plugin_manager.py
│       ├── models/               ← Entity, DeviceInfo
│       ├── mqtt/                 ← Paho + aiomqtt clients + base classes
│       ├── types.py              ← PublishPayload, StateValue
│       ├── exceptions.py
│       └── utils/
├── tests/
├── pyproject.toml
└── README.md
```

---

## Testing

Run all tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=ha_mqtt_sdk
```

---

## Docker

The repository includes a complete Docker environment for development and testing.

```bash
docker compose up --build
```

This starts:

- MQTT Broker (Mosquitto)
- SDK container
- Automated test execution

---

## Logging

The SDK uses a centralised logging system:

```python
from ha_mqtt_sdk.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Integration started")
```

---

## Development

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the full quality pipeline:

```bash
ruff check .
ruff format . --check
mypy src/ha_mqtt_sdk
pytest --cov=ha_mqtt_sdk
```

---

## License

MIT License — see the LICENSE file for details.

---

## Author

Dick Kouwenhoven

GitHub: https://github.com/dickkouwenhoven/HA-MQTT-SDK
