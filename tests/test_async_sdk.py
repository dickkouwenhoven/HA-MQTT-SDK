from unittest.mock import AsyncMock

import pytest

from ha_mqtt_sdk.builders.topic_manager import build_command_topic
from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.core.async_entity_manager import (
    AsyncEntityManager,
)
from ha_mqtt_sdk.exceptions import EntityError, MQTTError
from ha_mqtt_sdk.models.entity import Entity
from ha_mqtt_sdk.mqtt.async_client import AsyncMQTTClient

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

    config = MQTTSettings(
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

    config = MQTTSettings(
        host="localhost",
        port=1883,
    )

    client = AsyncMQTTClient(config)
    client._client = AsyncMock()

    await client.subscribe("test/topic")

    client._client.subscribe.assert_awaited_once_with("test/topic")


# ------------------------------------
# Entity manager tests
# ------------------------------------


@pytest.mark.asyncio
async def test_async_register_entity():

    mqtt = AsyncMockMQTTClient()

    manager = AsyncEntityManager(mqtt, MQTTSettings(discovery_prefix="homeassistant"))

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

    manager = AsyncEntityManager(mqtt, MQTTSettings(discovery_prefix="homeassistant"))

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

    manager = AsyncEntityManager(mqtt, MQTTSettings(discovery_prefix="homeassistant"))

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

    manager = AsyncEntityManager(mqtt, MQTTSettings(discovery_prefix="homeassistant"))

    entity = Entity(
        domain=HADomain.SWITCH,
        name="Switch",
        unique_id="switch_1",
    )

    called = {"value": False}

    async def callback(topic, payload):
        called["value"] = True

    await manager.register(
        entity,
        command_callback=callback,
    )

    await manager._handle_command(
        "homeassistant/switch/switch_1/set",
        "ON",
    )

    assert called["value"] is True


@pytest.mark.asyncio
async def test_async_sensor_not_subscribed():
    mqtt = AsyncMockMQTTClient()
    manager = AsyncEntityManager(mqtt, MQTTSettings())

    entity = Entity(
        domain=HADomain.SENSOR,
        name="Temperature",
        unique_id="temp_1",
    )

    await manager.register(entity)

    assert mqtt.subscribed == []


@pytest.mark.asyncio
async def test_async_switch_subscribed():

    mqtt = AsyncMockMQTTClient()

    manager = AsyncEntityManager(mqtt, MQTTSettings())

    entity = Entity(
        domain=HADomain.SWITCH,
        name="Switch",
        unique_id="switch_1",
    )

    await manager.register(entity)

    assert mqtt.subscribed == ["homeassistant/switch/switch_1/set"]


@pytest.mark.asyncio
async def test_async_register_invalid_entity():

    mqtt = AsyncMockMQTTClient()

    manager = AsyncEntityManager(mqtt, MQTTSettings())

    with pytest.raises(EntityError):
        await manager.register("invalid")


@pytest.mark.asyncio
async def test_async_command_without_callback():

    mqtt = AsyncMockMQTTClient()

    manager = AsyncEntityManager(mqtt, MQTTSettings())

    await manager._handle_command(
        "unknown/topic",
        "ON",
    )


@pytest.mark.asyncio
async def test_async_update_state_invalid_entity():

    mqtt = AsyncMockMQTTClient()

    manager = AsyncEntityManager(
        mqtt,
        MQTTSettings(),
    )

    with pytest.raises(EntityError):
        await manager.update_state(
            "invalid",
            "22.5",
        )


@pytest.mark.asyncio
async def test_async_update_availability_invalid_entity():
    mqtt = AsyncMockMQTTClient()

    manager = AsyncEntityManager(
        mqtt,
        MQTTSettings(),
    )

    with pytest.raises(EntityError):
        await manager.update_availability(
            "invalid",
            True,
        )


@pytest.mark.asyncio
async def test_async_set_command_callback():

    mqtt = AsyncMockMQTTClient()

    manager = AsyncEntityManager(mqtt, MQTTSettings())

    entity = Entity(
        domain=HADomain.SWITCH,
        name="Switch",
        unique_id="switch_1",
    )

    async def callback(topic, payload):
        pass

    manager.set_command_callback(
        entity,
        callback,
    )

    topic = build_command_topic(
        entity.domain,
        entity.unique_id,
        "homeassistant",
    )

    assert topic in manager._command_callbacks
