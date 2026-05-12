---

# 📄 **ROOT README.md (BELANGRIJK)**

Hier een professionele versie 👇

```markdown
# Home Assistant MQTT SDK

A professional, vendor-agnostic SDK for integrating devices with Home Assistant via MQTT.

---

## Features

- Automatic MQTT topic generation
- Home Assistant discovery support
- State & availability management
- Command handling (HA → device)
- Schema validation
- Fully tested (pytest + coverage)

---

## Installation

```bash
pip install hasdk

# Quick Start

from sdk.core.entity_manager import EntityManager
from sdk.config.domains import HADomain
from sdk.config.mqtt import MQTTSettings

mqtt = MyMQTTClient()
manager = EntityManager(
	mqtt,
	MQTTSettings(
		discovery_prefix="homeassistant"
	)
)

entity = manager.create_entity(
	domain=HADomain.LIGHT,
	name="Lamp",
	unique_id="lamp_1"
)

manager.register(entity)
manager.update_state(entity, "ON")
manager.update_availability(entity, True)

# Architecture
. SDK is vendor-independent
. Integrations (Dirigera, Hue, etc.) are seperate

# Testing
Bash
pytest --cov=sdk

# License
MIT


