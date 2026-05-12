# Home Assistant MQTT SDK

Python SDK voor Home Assistant MQTT integration.

**Features:**
- Support for all HA device types
- Factory functions for entities and discovery payloads
- Topic management and MQTT publish helpers
- Central logging (dual-mode: use existing logger or own logger)
- Full validation from required and optional fields
- Testable and Docker-ready

**Installation:**

```bash
pip install ha-mqtt-sdk

Usage:

from ha-mqtt-sdk.models.entity import make_entity
from ha-mqtt-sdk.config.domains import HADomain
from ha-mqtt-sdk.mqtt.mqtt_client import MQTTClient

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
├── requirements.txt
├── ha-mqtt-sdk/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── domains.py
│   │   └── device_fields.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── entity.py
│   ├── mqtt/
│   │   ├── __init__.py
│   │   ├── mqtt_client.py
│   │   ├── topic_manager.py
│   │   └── discovery_payload.py
│   └── utils/
│       ├── __init__.py
│       └── logger.py
└── tests/
    ├── __init__.py
    └── test_sdk.py

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
