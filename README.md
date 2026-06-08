# Home Assistant MQTT SDK

Production-ready Python SDK for integrating devices and applications with Home Assistant through MQTT Discovery.

The SDK simplifies Home Assistant MQTT integration by automatically handling:

* MQTT Discovery payload generation
* MQTT topic management
* Entity registration
* State updates
* Availability updates
* Command handling
* Sync and Async MQTT clients

---

# Features

* Home Assistant MQTT Discovery support
* Automatic MQTT topic generation
* Entity validation
* Availability management
* Command callback handling
* Sync MQTT support using Paho MQTT
* Async MQTT support using aiomqtt
* Dependency injection support
* Docker support
* Extensive test coverage
* Production-ready architecture

---

# Requirements

* Python 3.13+
* MQTT Broker (Mosquitto recommended)
* Home Assistant with MQTT integration enabled

---

# Installation

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

# Quick Start

## MQTT Configuration

```python
from ha_mqtt_sdk import MQTTSettings

mqtt_config = MQTTSettings(
    host="localhost",
    port=1883,
)
```

---

## Create MQTT Client

```python
from ha_mqtt_sdk import PahoMQTTClient

client = PahoMQTTClient(mqtt_config)
```

---

## Create SDK Instance

```python
from ha_mqtt_sdk import HASDK

sdk = HASDK(
    mqtt_client=client,
)
```

---

# Sync Example

## Create Device Info
```python
device_info: DeviceInfo = {
    "identifiers": {
        ("serial", "ABC123")
    },
    "manufacturer": "IKEA",
    "model": "DIRIGERA",
}
```

## Create Entity

```python
from ha_mqtt_sdk import Entity
from ha_mqtt_sdk import HADomain

sensor = Entity(
    domain=HADomain.SENSOR,
    name="Temperature",
    unique_id="temp_1",
)
```

## Register Entity

```python
sdk.register(sensor)
```

Home Assistant will automatically discover the entity through MQTT Discovery.

---

## Update State

```python
sdk.update_state(
    sensor,
    {
        "temperature": 22.5
    }
)
```

---

## Register Command Callback

```python
def handle_command(topic, payload):
    print(
        f"Command received: {topic} -> {payload}"
    )

sdk.on_command(
    sensor,
    handle_command,
)
```

---

# Async Example

## Create Async MQTT Client

```python
from ha_mqtt_sdk import AsyncMQTTClient

client = AsyncMQTTClient(mqtt_config)
```

## Create Async Entity Manager

```python
from ha_mqtt_sdk import AsyncEntityManager

manager = AsyncEntityManager(
    client,
    mqtt_config,
)
```

## Create Device Info
```python
device_info: DeviceInfo = {
    "identifiers": {
        ("serial", "ABC123")
    },
    "manufacturer": "IKEA",
    "model": "DIRIGERA",
}
```

## Create Entity

```python
from ha_mqtt_sdk import Entity
from ha_mqtt_sdk import HADomain

entity = Entity(
    domain=HADomain.SWITCH,
    name="Relay",
    unique_id="relay_1",
)
```

## Register Entity

```python
await manager.register(entity)
```

## Update State

```python
await manager.update_state(
    entity,
    "ON",
)
```

## Update Availability

```python
await manager.update_availability(
    entity,
    True,
)
```

---

# Supported Entity Domains

The SDK supports Home Assistant entity domains through:

```python
from ha_mqtt_sdk import HADomain
```

Examples include:

```python
HADomain.SENSOR
HADomain.SWITCH
HADomain.LIGHT
HADomain.BINARY_SENSOR
```

The complete list is maintained in:

```text
ha_mqtt_sdk/config/domains.py
```

---

# Architecture

```text
Home Assistant
        │
        ▼
 MQTT Discovery
        │
        ▼
     HASDK
        │
 ┌──────┴──────┐
 ▼             ▼
Sync       Async
Manager    Manager
 │             │
 ▼             ▼
Paho MQTT   aiomqtt
```

---

# Project Structure

```text
HA-MQTT-SDK
├── examples/
├── ha_mqtt_sdk/
│   ├── builders/
│   ├── config/
│   ├── core/
│   ├── models/
│   ├── mqtt/
│   ├── utils/
│   ├── validators/
│   ├── plugin_interface.py
│   ├── plugin_manager.py
│   └── exceptions.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

# Docker

The repository includes a complete Docker environment for development and testing.

Build and start:

```bash
docker compose up --build
```

This starts:

* MQTT Broker (Mosquitto)
* SDK container
* Automated test execution

---

# Testing

Run all tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=ha_mqtt_sdk
```

---

# Logging

The SDK uses a centralized logging system.

Example:

```python
from ha_mqtt_sdk import get_logger

logger = get_logger(__name__)

logger.info("SDK started")
```

---

# Development

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

---

# License

MIT License

See the LICENSE file for details.

---

# Author

Dick Kouwenhoven

GitHub:
https://github.com/dickkouwenhoven/HA-MQTT-SDK
