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

Install from source:

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

## Updating or Removing Entities (Discovery Changes)

Home Assistant MQTT Discovery is driven entirely by what gets published to
the discovery topic. The SDK reflects this directly — there is no separate
"update" operation. Changing a device means re-publishing its discovery
payload; removing a device means publishing an empty payload.

### Adding a new device after startup

Simply call `create_entity()` and `register()` at any point — not just at
startup. This is exactly what happens when a plugin's `setup()` discovers
a newly-added device:

```python
new_entity = sdk.create_entity(
    domain=HADomain.SENSOR,
    name="New Sensor",
    unique_id="sensor_new_1",
)
sdk.register(new_entity)
```

Home Assistant picks up the new discovery payload automatically — no
restart needed on either side.

### Changing an existing entity's configuration

Calling `register()` twice with the same `unique_id` raises `EntityError`:

```python
sdk.register(entity)
sdk.register(entity)  # raises EntityError: already registered
```

This is intentional — it prevents accidental duplicate registration. To
change an entity's configuration (for example, renaming it or changing its
`device_info`), unregister first, then register the updated version:

```python
sdk.unregister(entity)

updated_entity = sdk.create_entity(
    domain=HADomain.SENSOR,
    name="Renamed Sensor",       # ← new name
    unique_id="sensor_new_1",    # ← same unique_id
)
sdk.register(updated_entity)
```

`unregister()` publishes an empty payload to the discovery topic, which
tells Home Assistant to remove the entity. The subsequent `register()`
call publishes the new configuration, and HA re-creates the entity.

### Removing a device permanently

Call `unregister()` and do not re-register:

```python
sdk.unregister(entity)
```

This publishes an empty retained message to the discovery topic. Home
Assistant removes the entity from its registry. Because the message is
retained, the removal persists even if the MQTT broker restarts.

### Handling this in a plugin

If your hub reports that a device was removed or its configuration
changed, handle it inside your plugin's event loop:

```python
async def _on_hub_event(self, event: HubEvent) -> None:
    if event.type == "device_removed":
        entity = self._entities.pop(event.device_id, None)
        if entity:
            await self._sdk.unregister(entity)

    elif event.type == "device_renamed":
        old_entity = self._entities.get(event.device_id)
        if old_entity:
            await self._sdk.unregister(old_entity)

        new_entity = self._sdk.create_entity(
            domain=old_entity.domain,
            name=event.new_name,
            unique_id=event.device_id,
        )
        await self._sdk.register(new_entity, command_callback=self.handle_command)
        self._entities[event.device_id] = new_entity
```

### Summary

| Scenario | Action |
|---|---|
| New device discovered | `create_entity()` + `register()` |
| Device configuration changed | `unregister()` then `register()` with new config |
| Device removed from hub | `unregister()` only |
| Hub goes offline | `update_availability(entity, False)` — keeps entity registered, marks unavailable |
| Hub comes back online | `update_availability(entity, True)` |

Note the distinction between **availability** and **registration**: a
temporarily offline device should use `update_availability()`, not
`unregister()`. Unregistering removes the entity from HA entirely;
marking it unavailable just greys it out while keeping its history and
configuration intact.

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

## Adding a New Entity Domain to the SDK

This section is for SDK contributors who want to add support for a Home
Assistant domain not yet covered by `HADomain` — not for end users adding
device instances (see "Updating or Removing Entities" above for that).

The SDK currently supports these domains out of the box:

```python
from ha_mqtt_sdk import HADomain

HADomain.SENSOR
HADomain.SWITCH
HADomain.LIGHT
HADomain.BINARY_SENSOR
HADomain.CLIMATE
HADomain.COVER
HADomain.LOCK
HADomain.FAN
# ... and more — see ha_mqtt_sdk/config/domains.py for the full list
```

If Home Assistant adds a new MQTT integration domain, or you need one that
is not yet in this list, follow these three steps. All domain knowledge
lives in exactly two files — there is no need to touch the managers,
builders, or SDK entry points.

### Step 1 — Add the domain to `HADomain`

Edit `ha_mqtt_sdk/config/domains.py`:

```python
class HADomain(StrEnum):
    ...
    SIREN = "siren"
    YOUR_NEW_DOMAIN = "your_new_domain"  # ← add here, alphabetically
    SWITCH = "switch"
    ...
```

The string value must match exactly what Home Assistant expects in the
MQTT discovery topic, e.g. `homeassistant/<domain>/<unique_id>/config`.
Check the [Home Assistant MQTT integration docs](https://www.home-assistant.io/integrations/#search/mqtt)
for the correct domain string.

### Step 2 — Define its field schema

Edit `ha_mqtt_sdk/config/device_fields.py` and add an entry to
`ALLOWED_FIELDS_PER_DOMAIN`:

```python
ALLOWED_FIELDS_PER_DOMAIN: dict[HADomain, dict[str, set[str]]] = {
    ...
    HADomain.YOUR_NEW_DOMAIN: {
        "required": {"name", "unique_id"},
        "optional": _optional(
            COMMON_FIELDS,
            STATE_FIELDS,      # include if the domain reports state
            COMMAND_FIELDS,    # include if the domain accepts commands
            {
                # domain-specific fields go here, e.g.:
                "min_value",
                "max_value",
            },
        ),
    },
    ...
}
```

Three building blocks are available:
- `COMMON_FIELDS` — availability, device info, icon, etc. (almost always include)
- `STATE_FIELDS` — `state_topic`, `value_template`, etc. (include if the domain has a state)
- `COMMAND_FIELDS` — `command_topic`, `payload_on`/`payload_off`, etc. (include if the domain accepts commands)

Check the [Home Assistant MQTT discovery schema](https://www.home-assistant.io/integrations/mqtt/)
for the exact field names supported by your new domain.

### Step 3 — Verify topic generation works automatically

No changes are needed in `ha_mqtt_sdk/builders/topic_manager.py` — topic
building (`build_discovery_topic`, `build_state_topic`,
`build_command_topic`, `build_availability_topic`) is fully generic and
works for any `HADomain` value, since `command_topic` support is derived
automatically from whether `"command_topic"` appears in your domain's
`required` or `optional` set in Step 2.

### Step 4 — Write tests

Add coverage in `tests/models/test_entity.py` and
`tests/core/test_entity_factory.py` following the existing pattern:

```python
def test_create_your_new_domain_entity():
    entity = create_entity(
        domain=HADomain.YOUR_NEW_DOMAIN,
        name="Test Device",
        unique_id="test_1",
    )
    assert entity.domain == HADomain.YOUR_NEW_DOMAIN


def test_your_new_domain_registration(mqtt_client_sync):
    manager = EntityManager(mqtt_client_sync, MQTTSettings(discovery_prefix="homeassistant"))
    entity = manager.create_entity(
        domain=HADomain.YOUR_NEW_DOMAIN,
        name="Test Device",
        unique_id="test_1",
    )
    manager.register(entity)

    topic, payload, retain = mqtt_client_sync.published[0]
    assert topic.endswith("/config")
    assert payload["name"] == "Test Device"
```

### Summary

| Step | File | What changes |
|---|---|---|
| 1 | `config/domains.py` | Add enum member |
| 2 | `config/device_fields.py` | Add field schema entry |
| 3 | `builders/topic_manager.py` | Nothing — works automatically |
| 4 | `tests/` | Add coverage for the new domain |

No changes are ever needed in `EntityManager`, `AsyncEntityManager`,
`HASDK`, or `AsyncHASDK` — the schema-driven design means domain support
is entirely data, not code.

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
