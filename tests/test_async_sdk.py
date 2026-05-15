import pytest

from unittest.mock import AsyncMock

from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.config.mqtt import MQTTSettings

from ha_mqtt_sdk.models.entity import Entity

from ha_mqtt_sdk.core.async_entity_manager import (
	AsyncEntityManager,
)

from ha_mqtt_sdk.mqtt.async_client import AsyncMQTTClient
from ha_mqtt_sdk.mqtt.config import MQTTConfig

from ha_mqtt_sdk.exceptions import MQTTError
from .conftest import AsyncMockMQTTClient


# ------------------------------------
# MQTT client tests
# ------------------------------------

@pytest.mark.asyncio
async def test_async_publish():
	client = AsyncMockMQTTClient()

	await client.publish(
		"homeassistant/test_sensor/config",
		{"name": "Test Sensor"},
	)

	assert client.published


@pytest.mark.asyncio
async def test_async_publish_without_connection():

	config = MQTTConfig(
		host="localhost",
		port=1883,
	)

	client = AsyncMQTTClient(config)

	with pytest.raises(MQTTError):
		await client.publish(
			"test/topic",
			"hello",
		)


@pytest.mark.asyncio
async def test_async_subscribe():

	config = MQTTConfig(
		host="localhost",
		port=1883,
	)

	client = AsyncMQTTClient(config)

	await client.subscribe("test/topic")

	assert "test/topic" in client.subscribed
	

# ------------------------------------
# Entity manager tests
# ------------------------------------

@pytest.mark.asyncio
async def test_async_register_entity():

	mqtt = AsyncMockMQTTClient()

	manager = AsyncEntityManager(
		mqtt,
		MQTTSettings(
			discovery_prefix="homeassistant"
		)
	)

	entity = Entity(
		domain=HADomain.LIGHT,
		name="Kitchen Lamp",
		unique_id="kitchen_lamp_1",
	)

	await manager.register(entity)

	assert mqtt.published


@pytest.mark.asyncio
async def test_async_update_state():

	mqtt = AsyncMockMQTTClient()

	manager = AsyncEntityManager(
		mqtt,
		MQTTSettings(
			discovery_prefix="homeassistant"
		)
	)

	entity = Entity(
		domain=HADomain.SENSOR,
		name="Temperature",
		unique_id="temp_1",
	)

	await manager.update_state(
		entity,
		"22.5",
	)

	assert mqtt.published[-1][1] == "22.5"


@pytest.mark.asyncio
async def test_async_update_availability():

	mqtt = AsyncMockMQTTClient()

	manager = AsyncEntityManager(
		mqtt,
		MQTTSettings(
			discovery_prefix="homeassistant"
		)
	)

	entity = Entity(
		domain=HADomain.SWITCH,
		name="Relay",
		unique_id="relay_1",
	)

	await manager.update_availability(
		entity,
		True,
	)

	assert mqtt.published[-1][1] == "online"


# ------------------------------------
# Command callback handling
# ------------------------------------

@pytest.mark.asyncio
async def test_async_command_callback():

	mqtt = AsyncMockMQTTClient()

	manager = AsyncEntityManager(
		mqtt,
		MQTTSettings(
			discovery_prefix="homeassistant"
		)
	)

	called = {"value": False}
	
	async def callback(topic, payload):
		called["value"] = True
		
	manager._command_callbacks["test/topic"] = callback

	await manager._handle_command(
		"test/topic",
		"ON",
	)

	assert called["value"] is True
	
