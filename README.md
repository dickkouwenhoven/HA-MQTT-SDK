# Home Assistant MQTT SDK

Python SDK for Home Assistant MQTT integration.

**Features:**
- Support for all HA device types
- Factory functions for entities and discovery payloads
- Topic management and MQTT publish helpers
- Central logging (dual-mode: use existing logger or own logger)
- Full validation from required and optional fields
- Testable and Docker-ready

**Installation:**

```bash
pip install ha_mqtt_sdk

Usage:

from ha_mqtt_sdk.models.entity import make_entity
from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.mqtt.mqtt_client import MQTTClient

# Creation of an Entity
sensor = make_entity(HADomain.SENSOR, "Temperature Sensor", state_topic="sensor/temp")

# MQTT client
client = MQTTClient(host="localhost")
client.publish_discovery("homeassistant/sensor/temp/config", sensor)

Projectstructure:

HA-MQTT-SDK/
├── README.md
├── .gitignore
├── .env.example
├── setup.py
├── pyproject.toml
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── mosquitto.conf
├── setup.py
├── pyproject.toml
├── .github
│   └── workflows/
│       └── ci.yml
├── examples
│   └── basic_usage/
│       ├── README.md
│       └── main.py
├── ha_mqtt_sdk/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── plugin_interface.py
│   ├── plugin_manager.py
│   ├── builders/
│   │   ├── __init__.py
│   │   ├── discovery_payload.py
│   │   └── topic_manager.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── domains.py
│   │   ├── mqtt.py
│   │   └── device_fields.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── async_entity_manager.py
│   │   ├── entity_factory.py
│   │   ├── entity_manager.py
│   │   └── sdk.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── device_info.py
│   │   ├── entity.py
│   ├── mqtt/
│   │   ├── __init__.py
│   │   ├── async_client.py
│   │   ├── base.py
│   │   └── paho_client.py
│   └── utils/
│       ├── __init__.py
│       └── logger.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_async_sdk.py
    ├── test_discovery_payload.py
    ├── test_entity.py
    ├── test_entity_manager.py
    ├── test_sdk.py
    └── test_topic_manager.py

🚀 Usage
Start everything:
docker-compose up --build
🔍 Wat happens?

Mosquitto broker start

SDK container will be build

Tests runs automatically

MQTT communication is tested against real broker

🧪 Optional: Live debug mode

If you want to test interactively:

command: tail -f /dev/null

Then:

docker exec -it ha_mqtt_sdk bash
