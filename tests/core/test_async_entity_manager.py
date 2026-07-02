from unittest.mock import patch

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

# ------------------------------------------------
# Helpers
# ------------------------------------------------


def make_manager(mqtt_client_async, prefix: str = "homeassistant") -> AsyncEntityManager:
    return AsyncEntityManager(mqtt_client_async, MQTTSettings(discovery_prefix=prefix))


def make_sensor(manager: AsyncEntityManager, unique_id: str = "temp_1"):
    return manager.create_entity(domain=HADomain.SENSOR, name="Temp", unique_id=unique_id)


def make_switch(manager: AsyncEntityManager, unique_id: str = "switch_1"):
    return manager.create_entity(domain=HADomain.SWITCH, name="Switch", unique_id=unique_id)


def make_device_trigger(manager: AsyncEntityManager, unique_id: str = "trigger_1"):
    return manager.create_entity(
        domain=HADomain.DEVICE_TRIGGER, name="Trigger", unique_id=unique_id
    )


# ------------------------------------------------
# Init
# ------------------------------------------------


def test_init_invalid_mqtt_client_raises(mqtt_client_async):
    """Line 40: non-BaseAsyncMQTTClient must raise EntityError."""
    with pytest.raises(EntityError):
        AsyncEntityManager("not_a_client", MQTTSettings())


def test_init_invalid_mqtt_settings_raises(mqtt_client_async):
    """Line 42: non-MQTTSettings must raise EntityError."""
    with pytest.raises(EntityError):
        AsyncEntityManager(mqtt_client_async, "invalid")


# ------------------------------------------------
# Create_entity
# ------------------------------------------------


def test_create_entity(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)

    assert entity.unique_id == "temp_1"
    assert entity.domain == HADomain.SENSOR


# ------------------------------------------------
# Register
# ------------------------------------------------


@pytest.mark.asyncio
async def test_register_publishes_discovery_payload(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_switch(manager)

    await manager.register(entity)

    topic, payload, retain = mqtt_client_async.published[0]
    assert topic.endswith("/config")
    assert retain is True
    assert payload["name"] == "Switch"
    assert payload["unique_id"] == "switch_1"


@pytest.mark.asyncio
async def test_register_invalid_entity_raises(mqtt_client_async):
    manager = make_manager(mqtt_client_async)

    with pytest.raises(EntityError):
        await manager.register("invalid")


@pytest.mark.asyncio
async def test_register_duplicate_entity_raises(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)

    await manager.register(entity)

    with pytest.raises(EntityError):
        await manager.register(entity)


@pytest.mark.asyncio
async def test_register_switch_subscribes_to_command_topic(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_switch(manager)

    await manager.register(entity)

    expected = build_command_topic(entity.domain, entity.unique_id, "homeassistant")
    assert expected in mqtt_client_async.subscribed


@pytest.mark.asyncio
async def test_register_sensor_does_not_subscribe(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)

    await manager.register(entity)

    assert mqtt_client_async.subscribed == []


@pytest.mark.asyncio
async def test_register_sensor_sets_last_will(mqtt_client_async):
    """Line 129->137: LWT set for sensor — no command topic branch taken."""
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)

    await manager.register(entity)

    assert mqtt_client_async.last_will is not None
    assert mqtt_client_async.subscribed == []


@pytest.mark.asyncio
async def test_register_stores_command_callback(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_switch(manager)

    async def cb(topic: str, payload: str) -> None:
        pass

    await manager.register(entity, command_callback=cb)

    assert len(manager._command_callbacks) == 1
    assert next(iter(manager._command_callbacks.values())) is cb


@pytest.mark.asyncio
async def test_register_with_callback_executes_on_message(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_switch(manager)
    called = {"value": False}

    async def cb(topic: str, payload: str) -> None:
        called["value"] = True

    await manager.register(entity, command_callback=cb)

    expected = build_command_topic(entity.domain, entity.unique_id, "homeassistant")
    await mqtt_client_async.simulate_message(expected, "ON")

    assert called["value"] is True


@pytest.mark.asyncio
async def test_register_without_lwt_support_still_subscribes(mqtt_client_async_minimal):
    """Line 129->137: client without set_last_will skips LWT but still subscribes."""
    manager = AsyncEntityManager(
        mqtt_client_async_minimal, MQTTSettings(discovery_prefix="homeassistant")
    )
    entity = manager.create_entity(domain=HADomain.SWITCH, name="Switch", unique_id="switch_1")

    await manager.register(entity)

    assert not hasattr(mqtt_client_async_minimal, "set_last_will")
    expected = build_command_topic(entity.domain, entity.unique_id, "homeassistant")
    assert expected in mqtt_client_async_minimal.subscribed


# ------------------------------------------------
# Update_state
# ------------------------------------------------


@pytest.mark.asyncio
async def test_update_state(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)

    await manager.register(entity)
    await manager.update_state(entity, 25)

    topic, payload, retain = mqtt_client_async.published[-1]
    expected = build_state_topic(entity.domain, entity.unique_id, "homeassistant")
    assert topic == expected
    assert payload == 25


@pytest.mark.asyncio
async def test_update_state_invalid_entity_raises(mqtt_client_async):
    manager = make_manager(mqtt_client_async)

    with pytest.raises(EntityError):
        await manager.update_state("invalid", 25)


@pytest.mark.asyncio
async def test_update_state_unregistered_entity_raises(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)

    with pytest.raises(EntityError, match="is not registered"):
        await manager.update_state(entity, 25)


@pytest.mark.asyncio
async def test_update_state_state_topic_not_supported(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_switch(manager)

    await manager.register(entity)

    registration = build_registration(entity, manager._settings.discovery_prefix)
    registration.state_topic = None

    with (
        patch(
            "ha_mqtt_sdk.core.async_entity_manager.build_registration",
            return_value=registration,
        ),
        pytest.raises(EntityError, match="does not support state updates"),
    ):
        await manager.update_state(entity, 25)


# ------------------------------------------------
# Update_availability
# ------------------------------------------------


@pytest.mark.asyncio
async def test_update_availability_online(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)

    await manager.register(entity)
    await manager.update_availability(entity, True)

    topic, payload, retain = mqtt_client_async.published[-1]
    expected = build_availability_topic(entity.domain, entity.unique_id, "homeassistant")
    assert topic == expected
    assert payload == "online"
    assert retain is True


@pytest.mark.asyncio
async def test_update_availability_offline(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)

    await manager.register(entity)
    await manager.update_availability(entity, False)

    _, payload, _ = mqtt_client_async.published[-1]
    assert payload == "offline"


@pytest.mark.asyncio
async def test_update_availability_invalid_entity_raises(mqtt_client_async):
    manager = make_manager(mqtt_client_async)

    with pytest.raises(EntityError):
        await manager.update_availability("invalid", True)


@pytest.mark.asyncio
async def test_update_availability_unregistered_entity_raises(mqtt_client_async):
    """Line 196: unregistered entity must raise."""
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)

    with pytest.raises(EntityError):
        await manager.update_availability(entity, True)


@pytest.mark.asyncio
async def test_update_availability_availability_topic_not_supported(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_device_trigger(manager)

    await manager.register(entity)

    registration = build_registration(entity, manager._settings.discovery_prefix)
    registration.availability_topic = None

    with (
        patch(
            "ha_mqtt_sdk.core.async_entity_manager.build_registration",
            return_value=registration,
        ),
        pytest.raises(EntityError, match="does not support availability updates"),
    ):
        await manager.update_availability(entity, True)


# ------------------------------------------------
# Set_command_callback
# ------------------------------------------------


@pytest.mark.asyncio
async def test_set_command_callback_replaces_existing(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_switch(manager)
    first_called = {"value": False}
    second_called = {"value": False}

    async def cb1(topic: str, payload: str) -> None:
        first_called["value"] = True

    async def cb2(topic: str, payload: str) -> None:
        second_called["value"] = True

    await manager.register(entity, command_callback=cb1)
    await manager.set_command_callback(entity, cb2)

    expected = build_command_topic(entity.domain, entity.unique_id, "homeassistant")
    await mqtt_client_async.simulate_message(expected, "ON")

    assert first_called["value"] is False
    assert second_called["value"] is True


@pytest.mark.asyncio
async def test_set_command_callback_invalid_entity_raises(mqtt_client_async):
    """Line 229: non-Entity must raise."""
    manager = make_manager(mqtt_client_async)

    async def cb(topic: str, payload: str) -> None:
        pass

    with pytest.raises(EntityError):
        await manager.set_command_callback("invalid", cb)


@pytest.mark.asyncio
async def test_set_command_callback_non_callable_raises(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_switch(manager)
    await manager.register(entity)

    with pytest.raises(EntityError):
        await manager.set_command_callback(entity, "not_callable")  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_set_command_callback_unregistered_entity_raises(mqtt_client_async):
    """Line 235: entity not in registry must raise."""
    manager = make_manager(mqtt_client_async)
    entity = make_switch(manager)

    async def cb(topic: str, payload: str) -> None:
        pass

    with pytest.raises(EntityError):
        await manager.set_command_callback(entity, cb)


@pytest.mark.asyncio
async def test_set_command_callback_on_sensor_raises(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)
    await manager.register(entity)

    with pytest.raises(EntityError, match="does not support commands"):
        await manager.set_command_callback(entity, lambda t, p: None)


# ------------------------------------------------
# _Handle_command
# ------------------------------------------------


@pytest.mark.asyncio
async def test_handle_command_no_callback_registered(mqtt_client_async):
    manager = make_manager(mqtt_client_async)

    await manager._handle_command("unknown/topic", "ON")  # must not raise


@pytest.mark.asyncio
async def test_handle_command_callback_exception_is_caught(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_switch(manager)

    async def bad_cb(topic: str, payload: str) -> None:
        raise RuntimeError("boom")

    await manager.register(entity, command_callback=bad_cb)

    expected = build_command_topic(entity.domain, entity.unique_id, "homeassistant")
    await mqtt_client_async.simulate_message(expected, "ON")  # must not raise


# ------------------------------------------------
# _Is_registered
# ------------------------------------------------


@pytest.mark.asyncio
async def test_is_registered_true(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)
    await manager.register(entity)

    assert manager.is_registered(entity) is True


def test_is_registered_false(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)

    assert manager.is_registered(entity) is False


def test_is_registered_invalid_entity_raises(mqtt_client_async):
    """Line 295: non-Entity must raise."""
    manager = make_manager(mqtt_client_async)

    with pytest.raises(EntityError):
        manager.is_registered("invalid")


# ------------------------------------------------
# _Get_entity
# ------------------------------------------------


@pytest.mark.asyncio
async def test_get_entity_found(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)
    await manager.register(entity)

    assert manager.get_entity("temp_1") is entity


def test_get_entity_not_found(mqtt_client_async):
    manager = make_manager(mqtt_client_async)

    assert manager.get_entity("unknown") is None


@pytest.mark.parametrize("unique_id", ["", "   "])
def test_get_entity_invalid_unique_id_raises(mqtt_client_async, unique_id):
    manager = make_manager(mqtt_client_async)

    with pytest.raises(EntityError):
        manager.get_entity(unique_id)


# ------------------------------------------------
# Unregister
# ------------------------------------------------


@pytest.mark.asyncio
async def test_unregister_removes_entity(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)

    await manager.register(entity)
    assert manager.is_registered(entity)

    await manager.unregister(entity)
    assert not manager.is_registered(entity)


@pytest.mark.asyncio
async def test_unregister_publishes_empty_discovery(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)

    await manager.register(entity)
    await manager.unregister(entity)

    topic, payload, retain = mqtt_client_async.published[-1]
    assert topic.endswith("/config")
    assert payload == ""
    assert retain is True


@pytest.mark.asyncio
async def test_unregister_removes_command_callback(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_switch(manager)

    async def cb(topic: str, payload: str) -> None:
        pass

    await manager.register(entity, command_callback=cb)

    registration = build_registration(entity, manager._settings.discovery_prefix)
    assert registration.command_topic in manager._command_callbacks

    await manager.unregister(entity)
    assert registration.command_topic not in manager._command_callbacks


@pytest.mark.asyncio
async def test_unregister_invalid_entity_raises(mqtt_client_async):
    manager = make_manager(mqtt_client_async)

    with pytest.raises(EntityError):
        await manager.unregister("invalid")


@pytest.mark.asyncio
async def test_unregister_unregistered_entity_raises(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)

    with pytest.raises(EntityError):
        await manager.unregister(entity)


@pytest.mark.asyncio
async def test_unregister_twice_raises(mqtt_client_async):
    manager = make_manager(mqtt_client_async)
    entity = make_sensor(manager)

    await manager.register(entity)
    await manager.unregister(entity)

    with pytest.raises(EntityError):
        await manager.unregister(entity)
