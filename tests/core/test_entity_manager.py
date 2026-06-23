import pytest

from ha_mqtt_sdk.builders.topic_manager import (
    build_availability_topic,
    build_command_topic,
    build_state_topic,
)
from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.core.entity_manager import EntityManager
from ha_mqtt_sdk.exceptions import EntityError

# -----------------------------------------------------
# Helpers
# -----------------------------------------------------


def make_manager(mqtt_client_sync, prefix: str = "homeassistant") -> EntityManager:
    return EntityManager(mqtt_client_sync, MQTTSettings(discovery_prefix=prefix))


def make_switch(manager: EntityManager, unique_id: str = "switch_1") -> object:
    return manager.create_entity(
        domain=HADomain.SWITCH, name="Switch", unique_id=unique_id
    )


def make_sensor(manager: EntityManager, unique_id: str = "temp_1") -> object:
    return manager.create_entity(
        domain=HADomain.SENSOR, name="Temp", unique_id=unique_id
    )


# ------------------------------------------------------
# Init
# ------------------------------------------------------


def test_init_invalid_mqtt_client_raises(mqtt_client_sync):
    """Line 55: non-BaseMQTTClient must raise EntityError."""
    with pytest.raises(EntityError):
        EntityManager("not_a_client", MQTTSettings())


def test_init_invalid_mqtt_settings_raises(mqtt_client_sync):
    """Line 58: non-MQTTSettings must raise EntityError."""
    with pytest.raises(EntityError):
        EntityManager(mqtt_client_sync, "not_settings")


# -------------------------------------------------------
# Create Entity
# -------------------------------------------------------


def test_create_entity(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)

    assert entity.unique_id == "temp_1"
    assert entity.domain == HADomain.SENSOR


# -------------------------------------------------------
# Register
# -------------------------------------------------------


def test_register_entity_publishes_discovery(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_switch(manager)

    manager.register(entity)

    topic, payload, retain = mqtt_client_sync.published[0]
    assert topic.endswith("/config")
    assert retain is True
    assert payload["name"] == "Switch"
    assert payload["unique_id"] == "switch_1"


def test_register_invalid_entity_raises(mqtt_client_sync):
    """Line: invalid entity guard in register."""
    manager = make_manager(mqtt_client_sync)

    with pytest.raises(EntityError):
        manager.register("invalid")


def test_register_duplicate_unique_id_raises(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity1 = make_sensor(manager, "temp_1")
    entity2 = make_sensor(manager, "temp_1")

    manager.register(entity1)

    with pytest.raises(EntityError):
        manager.register(entity2)


def test_register_same_entity_twice_raises(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)

    manager.register(entity)

    with pytest.raises(EntityError):
        manager.register(entity)


def test_register_switch_subscribes_to_command_topic(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_switch(manager)

    manager.register(entity)

    expected = build_command_topic(entity.domain, entity.unique_id, "homeassistant")
    assert expected in mqtt_client_sync.subscribed


def test_register_sensor_does_not_subscribe(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)

    manager.register(entity)

    assert mqtt_client_sync.subscribed == []


def test_register_calls_set_last_will(mqtt_client_sync):
    """Lines 148→156: LWT set for sensor (no command topic branch)."""
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)

    manager.register(entity)

    assert mqtt_client_sync.last_will_topic is not None


def test_register_with_command_callback(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_switch(manager)
    called = {"value": False}

    def callback(topic, payload):
        called["value"] = True

    manager.register(entity, command_callback=callback)

    expected = build_command_topic(entity.domain, entity.unique_id, "homeassistant")
    mqtt_client_sync.simulate_message(expected, "ON")

    assert called["value"] is True


# -----------------------------------------------------------
# Update_state
# -----------------------------------------------------------


def test_update_state(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)

    manager.register(entity)
    manager.update_state(entity, 25)

    topic, payload, retain = mqtt_client_sync.published[-1]
    expected = build_state_topic(entity.domain, entity.unique_id, "homeassistant")
    assert topic == expected
    assert payload == 25


def test_update_state_invalid_entity_raises(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)

    with pytest.raises(EntityError):
        manager.update_state("invalid", 25)


def test_update_state_unregistered_entity_raises(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)

    with pytest.raises(EntityError):
        manager.update_state(entity, 25)


# -----------------------------------------------------------
# Update_availability
# -----------------------------------------------------------


def test_update_availability_online(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)

    manager.register(entity)
    manager.update_availability(entity, True)

    topic, payload, retain = mqtt_client_sync.published[-1]
    expected = build_availability_topic(entity.domain, entity.unique_id, "homeassistant")
    assert topic == expected
    assert payload == "online"
    assert retain is True


def test_update_availability_offline(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)

    manager.register(entity)
    manager.update_availability(entity, False)

    _, payload, _ = mqtt_client_sync.published[-1]
    assert payload == "offline"


def test_update_availability_invalid_entity_raises(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)

    with pytest.raises(EntityError):
        manager.update_availability("invalid", True)


def test_update_availability_unregistered_entity_raises(mqtt_client_sync):
    """Line 219: unregistered entity must raise."""
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)

    with pytest.raises(EntityError):
        manager.update_availability(entity, True)


# -----------------------------------------------------------
# Set_command_callback
# -----------------------------------------------------------


def test_set_command_callback_replaces_existing(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_switch(manager)

    first_called = {"value": False}
    second_called = {"value": False}

    def callback_1(topic, payload):
        first_called["value"] = True

    def callback_2(topic, payload):
        second_called["value"] = True

    manager.register(entity, command_callback=callback_1)
    manager.set_command_callback(entity, callback_2)

    expected = build_command_topic(entity.domain, entity.unique_id, "homeassistant")
    mqtt_client_sync.simulate_message(expected, "ON")

    assert first_called["value"] is False
    assert second_called["value"] is True


def test_set_command_callback_invalid_entity_raises(mqtt_client_sync):
    """Line 254: non-Entity must raise."""
    manager = make_manager(mqtt_client_sync)

    with pytest.raises(EntityError):
        manager.set_command_callback("invalid", lambda t, p: None)


def test_set_command_callback_non_callable_raises(mqtt_client_sync):
    """Line 257: non-callable must raise."""
    manager = make_manager(mqtt_client_sync)
    entity = make_switch(manager)
    manager.register(entity)

    with pytest.raises(EntityError):
        manager.set_command_callback(entity, "not_callable")  # type: ignore[arg-type]


def test_set_command_callback_unregistered_entity_raises(mqtt_client_sync):
    """Line 268: unregistered entity must raise."""
    manager = make_manager(mqtt_client_sync)
    entity = make_switch(manager)

    with pytest.raises(EntityError):
        manager.set_command_callback(entity, lambda t, p: None)


def test_set_command_callback_on_sensor_raises(mqtt_client_sync):
    """Sensor has no command topic — must raise EntityError."""
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)
    manager.register(entity)

    with pytest.raises(EntityError):
        manager.set_command_callback(entity, lambda t, p: None)


# -----------------------------------------------------------
# Handle_command
# -----------------------------------------------------------


def test_handle_command_no_callback_registered(mqtt_client_sync):
    """Lines 303-307: unknown topic must log warning and not raise."""
    manager = make_manager(mqtt_client_sync)
    entity = make_switch(manager)
    manager.register(entity)

    mqtt_client_sync.simulate_message("unknown/topic", "ON")  # must not raise


def test_handle_command_callback_exception_is_caught(mqtt_client_sync):
    """Lines 311-312: callback exception must be caught and logged."""
    manager = make_manager(mqtt_client_sync)
    entity = make_switch(manager)

    def bad_callback(topic, payload):
        raise RuntimeError("boom")

    manager.register(entity, command_callback=bad_callback)

    expected = build_command_topic(entity.domain, entity.unique_id, "homeassistant")
    mqtt_client_sync.simulate_message(expected, "ON")  # must not raise


# -----------------------------------------------------------
# Is_registered
# -----------------------------------------------------------


def test_is_registered_true(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)
    manager.register(entity)

    assert manager.is_registered(entity) is True


def test_is_registered_false(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)

    assert manager.is_registered(entity) is False


def test_is_registered_invalid_entity_raises(mqtt_client_sync):
    """Line 323: non-Entity must raise."""
    manager = make_manager(mqtt_client_sync)

    with pytest.raises(EntityError):
        manager.is_registered("invalid")


# -----------------------------------------------------------
# Get_entity
# -----------------------------------------------------------


def test_get_entity_found(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)
    manager.register(entity)

    assert manager.get_entity("temp_1") is entity


def test_get_entity_not_found(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)

    assert manager.get_entity("unknown") is None


def test_get_entity_empty_unique_id_raises(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)

    with pytest.raises(EntityError):
        manager.get_entity("")


def test_get_entity_whitespace_unique_id_raises(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)

    with pytest.raises(EntityError):
        manager.get_entity("   ")


# -----------------------------------------------------------
# Unregister
# -----------------------------------------------------------


def test_unregister_removes_entity(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)

    manager.register(entity)
    assert manager.is_registered(entity)

    manager.unregister(entity)
    assert not manager.is_registered(entity)


def test_unregister_publishes_empty_discovery(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)

    manager.register(entity)
    manager.unregister(entity)

    topic, payload, retain = mqtt_client_sync.published[-1]
    assert topic.endswith("/config")
    assert payload == ""
    assert retain is True


def test_unregister_removes_command_callback(mqtt_client_sync):
    """Line 377: command callback must be cleaned up on unregister."""
    manager = make_manager(mqtt_client_sync)
    entity = make_switch(manager)

    manager.register(entity, command_callback=lambda t, p: None)

    expected = build_command_topic(entity.domain, entity.unique_id, "homeassistant")
    assert expected in manager._command_callbacks

    manager.unregister(entity)

    assert expected not in manager._command_callbacks


def test_unregister_invalid_entity_raises(mqtt_client_sync):
    """Line 358: non-Entity must raise."""
    manager = make_manager(mqtt_client_sync)

    with pytest.raises(EntityError):
        manager.unregister("invalid")


def test_unregister_unregistered_entity_raises(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)

    with pytest.raises(EntityError):
        manager.unregister(entity)


def test_unregister_twice_raises(mqtt_client_sync):
    manager = make_manager(mqtt_client_sync)
    entity = make_sensor(manager)

    manager.register(entity)
    manager.unregister(entity)

    with pytest.raises(EntityError):
        manager.unregister(entity)
