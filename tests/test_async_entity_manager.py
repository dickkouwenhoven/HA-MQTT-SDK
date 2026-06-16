import pytest

from ha_mqtt_sdk.builders.topic_manager import (
    build_availability_topic,
    build_command_topic,
    build_state_topic,
)
from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.core.async_entity_manager import AsyncEntityManager
from ha_mqtt_sdk.core.entity_factory import build_registration
from ha_mqtt_sdk.exceptions import EntityError


def test_create_entity(mqtt_client_async):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    assert entity.unique_id == "temp_1"
    assert entity.domain == HADomain.SENSOR


@pytest.mark.asyncio
async def test_register_entity(mqtt_client_async):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    entity = manager.create_entity(
        domain=HADomain.SWITCH,
        name="Switch",
        unique_id="switch_1",
    )

    await manager.register(entity)

    assert len(mqtt_client_async.published) > 0


@pytest.mark.asyncio
async def test_command_subscription(mqtt_client_async):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    entity = manager.create_entity(
        domain=HADomain.SWITCH,
        name="Switch",
        unique_id="switch_1",
    )

    await manager.register(entity)

    expected_topic = build_command_topic(
        entity.domain,
        entity.unique_id,
        "homeassistant",
    )

    assert expected_topic in mqtt_client_async.subscribed


@pytest.mark.asyncio
async def test_update_state(mqtt_client_async):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)
    await manager.update_state(entity, 25)

    assert mqtt_client_async.published[-1][1] == 25


@pytest.mark.asyncio
async def test_update_availability(mqtt_client_async):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)
    await manager.update_availability(entity, True)

    topic, payload, retain = mqtt_client_async.published[-1]

    assert payload == "online"
    assert retain is True


@pytest.mark.asyncio
async def test_command_callback_execution(mqtt_client_async):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    entity = manager.create_entity(
        domain=HADomain.SWITCH,
        name="Switch",
        unique_id="switch_1",
    )

    called = {"value": False}

    async def callback(topic, payload):
        called["value"] = True

    await manager.register(entity, command_callback=callback)

    # Simulate MQTT message
    expected_topic = build_command_topic(
        entity.domain,
        entity.unique_id,
        "homeassistant",
    )

    await mqtt_client_async.simulate_message(expected_topic, "ON")

    assert called["value"] is True


@pytest.mark.asyncio
async def test_sensor_has_no_command_subscription(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)

    assert mqtt_client_async.subscribed == []


@pytest.mark.asyncio
async def test_register_invalid_entity(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings())

    with pytest.raises(EntityError):
        await manager.register("invalid")


@pytest.mark.asyncio
async def test_update_state_invalid_entity(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings())

    with pytest.raises(EntityError):
        await manager.update_state(
            "invalid",
            25,
        )


@pytest.mark.asyncio
async def test_update_availability_invalid_entity(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings())

    with pytest.raises(EntityError):
        await manager.update_availability(
            "invalid",
            True,
        )


@pytest.mark.asyncio
async def test_set_callback_on_sensor_fails(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings())

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)

    with pytest.raises(EntityError, match="does not support commands"):
        await manager.set_command_callback(
            entity,
            lambda t, p: None,
        )


@pytest.mark.asyncio
async def test_duplicate_unique_id_fails(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings())

    entity1 = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp1",
        unique_id="temp_1",
    )

    entity2 = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp2",
        unique_id="temp_1",
    )

    await manager.register(entity1)

    with pytest.raises(EntityError):
        await manager.register(entity2)


@pytest.mark.asyncio
async def test_replace_command_callback(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings())

    entity = manager.create_entity(
        domain=HADomain.SWITCH,
        name="Switch",
        unique_id="switch_1",
    )

    first_called = {"value": False}
    second_called = {"value": False}

    async def callback_1(topic, payload):
        first_called["value"] = True

    async def callback_2(topic, payload):
        second_called["value"] = True

    await manager.register(
        entity,
        command_callback=callback_1,
    )

    await manager.set_command_callback(
        entity,
        callback_2,
    )

    expected_topic = build_command_topic(
        entity.domain,
        entity.unique_id,
        "homeassistant",
    )

    await mqtt_client_async.simulate_message(expected_topic, "ON")

    print("Dick is:",manager._command_callbacks.keys())

    assert first_called["value"] is False
    assert second_called["value"] is True


@pytest.mark.asyncio
async def test_update_state_topic(
    mqtt_client_async,
):
    manager = AsyncEntityManager(
        mqtt_client_async,
        MQTTSettings(discovery_prefix="homeassistant"),
    )

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)
    await manager.update_state(
        entity,
        25,
    )

    topic, payload, retain = mqtt_client_async.published[-1]

    expected_topic = build_state_topic(
        entity.domain,
        entity.unique_id,
        "homeassistant",
    )

    assert topic == expected_topic
    assert payload == 25


@pytest.mark.asyncio
async def test_update_availability_topic(
    mqtt_client_async,
):
    manager = AsyncEntityManager(
        mqtt_client_async,
        MQTTSettings(discovery_prefix="homeassistant"),
    )

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)
    await manager.update_availability(
        entity,
        True,
    )

    topic, payload, retain = mqtt_client_async.published[-1]

    expected_topic = build_availability_topic(
        entity.domain,
        entity.unique_id,
        "homeassistant",
    )

    assert topic == expected_topic
    assert payload == "online"
    assert retain is True


@pytest.mark.asyncio
async def test_register_publishers_discovery_payload(
    mqtt_client_async,
):
    manager = AsyncEntityManager(
        mqtt_client_async,
        MQTTSettings(discovery_prefix="homeassistant"),
    )

    entity = manager.create_entity(
        domain=HADomain.SWITCH,
        name="Switch",
        unique_id="switch_1",
    )

    await manager.register(entity)

    topic, payload, retain = mqtt_client_async.published[0]

    assert topic.endswith("/config")
    assert retain is True

    assert payload["name"] == "Switch"
    assert payload["unique_id"] == "switch_1"


@pytest.mark.asyncio
async def test_register_same_entity_twice_fails(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings())

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)

    with pytest.raises(EntityError):
        await manager.register(entity)


@pytest.mark.asyncio
async def test_update_state_unregistered_entity_fails(
    mqtt_client_async,
):
    manager = AsyncEntityManager(
        mqtt_client_async,
        MQTTSettings(),
    )

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    with pytest.raises(EntityError):
        await manager.update_state(
            entity,
            25,
        )


@pytest.mark.asyncio
async def test_get_entity(
    mqtt_client_async,
):
    manager = AsyncEntityManager(
        mqtt_client_async,
        MQTTSettings(),
    )

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)

    result = manager.get_entity("temp_1")

    assert result is entity


def test_get_entity_not_found(
    mqtt_client_async,
):
    manager = AsyncEntityManager(
        mqtt_client_async,
        MQTTSettings(),
    )

    assert manager.get_entity("unknown") is None


def test_get_entity_invalid_unique_id(
    mqtt_client_async,
):
    manager = AsyncEntityManager(
        mqtt_client_async,
        MQTTSettings(),
    )

    with pytest.raises(EntityError):
        manager.get_entity("")


@pytest.mark.asyncio
async def test_unregister_entity(
    mqtt_client_async,
):
    manager = AsyncEntityManager(
        mqtt_client_async,
        MQTTSettings(),
    )

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)

    assert manager.is_registered(entity)

    await manager.unregister(entity)

    assert not manager.is_registered(entity)


@pytest.mark.asyncio
async def test_unregister_publishes_empty_discovery(
    mqtt_client_async,
):
    manager = AsyncEntityManager(
        mqtt_client_async,
        MQTTSettings(),
    )

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)
    await manager.unregister(entity)

    topic, payload, retain = mqtt_client_async.published[-1]

    assert topic.endswith("/config")
    assert payload == ""
    assert retain is True


@pytest.mark.asyncio
async def test_unregister_removes_entity(
    mqtt_client_async,
):
    manager = AsyncEntityManager(
        mqtt_client_async,
        MQTTSettings(),
    )

    entity = manager.create_entity(
        domain=HADomain.SWITCH,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)

    assert manager.is_registered(entity)

    await manager.unregister(entity)

    assert not manager.is_registered(entity)


@pytest.mark.asyncio
async def test_unregister_twice_fails(
    mqtt_client_async,
):
    manager = AsyncEntityManager(
        mqtt_client_async,
        MQTTSettings(),
    )

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)
    await manager.unregister(entity)

    with pytest.raises(EntityError):
        await manager.unregister(entity)


def test_init_requires_mqtt_settings(mqtt_client_async):
    with pytest.raises(EntityError, match="mqtt_settings must be MQTTSettings"):
        AsyncEntityManager(
            mqtt_client=mqtt_client_async,
            mqtt_settings="invalid",
        )


@pytest.mark.asyncio
async def test_register_stores_command_callback(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    entity = manager.create_entity(
        domain=HADomain.SWITCH,
        name="Temp",
        unique_id="temp_1",
    )

    async def callback(topic, payload):
        pass

    await manager.register(
        entity,
        command_callback=callback,
    )

    assert len(manager._command_callbacks) == 1
    stored_callback = next(iter(manager._command_callbacks.values()))
    assert stored_callback is callback


@pytest.mark.asyncio
async def test_set_command_callback_requires_callable(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)

    with pytest.raises(EntityError, match="callback must be callable"):
        await manager.set_command_callback(
            entity,
            "not_a_function",
        )


@pytest.mark.asyncio
async def test_handle_command_without_registered_callback(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    await manager._handle_command(
        "test/topic",
        "payload",
    )


@pytest.mark.asyncio
async def test_handle_command_callback_exception(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    async def failing_callback(topic, payload):
        raise RuntimeError("boom")

    manager._command_callbacks["test/topic"] = failing_callback

    await manager._handle_command(
        "test/topic",
        "payload",
    )


@pytest.mark.parametrize(
    "unique_id",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_get_entity_requires_non_empty_string(
    mqtt_client_async,
    unique_id,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))
    with pytest.raises(
        EntityError,
        match="unique_id must be a non-empty string",
    ):
        manager.get_entity(unique_id)


def test_get_entity_returns_none_when_not_found(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    assert manager.get_entity("missing") is None


@pytest.mark.asyncio
async def test_get_entity_returns_registered_entity(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)

    assert manager.get_entity(entity.unique_id) is entity


@pytest.mark.asyncio
async def test_unregister_requires_entity_instance(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    with pytest.raises(EntityError, match="Invalid entity"):
        await manager.unregister("not_entity")


@pytest.mark.asyncio
async def test_unregister_removes_command_callback(
    mqtt_client_async,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    entity = manager.create_entity(
        domain=HADomain.SWITCH,
        name="Temp",
        unique_id="temp_1",
    )

    async def callback(topic, payload):
        pass

    await manager.register(
        entity,
        command_callback=callback,
    )

    registration = build_registration(
        entity,
        manager._settings.discovery_prefix,
    )

    assert registration.command_topic in manager._command_callbacks

    await manager.unregister(entity)

    assert registration.command_topic not in manager._command_callbacks


@pytest.mark.asyncio
async def test_unregister_logs_success(
    mqtt_client_async,
    caplog,
):
    manager = AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix="homeassistant"))

    entity = manager.create_entity(
        domain=HADomain.SENSOR,
        name="Temp",
        unique_id="temp_1",
    )

    await manager.register(entity)

    await manager.unregister(entity)

    assert "Entity unregistered" in caplog.text
