from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.core.async_sdk import AsyncHASDK

# from ha_mqtt_sdk.entity_factory import create_entity
# from ha_mqtt_sdk.exceptions import SDKError
# from ha_mqtt_sdk.models.entity import Entity
# from ha_mqtt_sdk.mqtt.async_client import AsyncMQTTClient
# -------------------------
# Init tests
# -------------------------


def test_init_requires_either_settings_or_client():
    with pytest.raises(SDKError):
        AsyncHASDK(async_mqtt_client=None, mqtt_settings=None)


@pytest.mark.asyncio
async def test_register_with_invalid_entity():
    mqtt_config = MQTTSettings(host="localhost", port=1883)
    client = AsyncMQTTClient(config=mqtt_config)
    sdk = AsyncHASDK(async_mqtt_client=client)

    with pytest.raises(SDKError):
        await sdk.register("Invalid Entity", None)


@pytest.mark.asyncio
async def test_update_state_with_invalid_entity():
    mqtt_config = MQTTSettings(
        host="localhost",
        port=1883,
    )

    client = AsyncMQTTClient(config=mqtt_config)

    sdk = AsyncHASDK(
        async_mqtt_client=client,
    )

    with pytest.raises(SDKError):
        await sdk.update_state("Invalid Entity", "ON")


@pytest.mark.asyncio
async def test_on_command_with_invalid_entity():
    mqtt_config = MQTTSettings(
        host="localhost",
        port=1883,
    )

    client = AsyncMQTTClient(config=mqtt_config)

    sdk = AsyncHASDK(
        async_mqtt_client=client,
    )

    async def dummy_callback(topic: str, payload: str) -> None:
        pass

    with pytest.raises(SDKError):
        await sdk.on_command("Invalid Entity", dummy_callback)


# ── helpers ──────────────────────────────────────────────────────────────────

def make_sdk(mock_manager: MagicMock) -> AsyncHASDK:
    """Build an AsyncHASDK with a mocked AsyncEntityManager."""
    mqtt_config = MQTTSettings(host="localhost", port=1883)
    client = AsyncMQTTClient(config=mqtt_config)
    with patch("ha_mqtt_sdk.core.async_sdk.AsyncEntityManager", return_value=mock_manager):
        return AsyncHASDK(async_mqtt_client=client)


def make_entity() -> Entity:
    return create_entity(domain=HADomain.SWITCH, name="Relay", unique_id="relay_1")


# ── line 50: init from mqtt_settings only (no injected client) ───────────────

def test_init_from_mqtt_settings_only():
    """Covers the else-branch that constructs AsyncMQTTClient internally (line 50)."""
    mqtt_config = MQTTSettings(host="localhost", port=1883)
    sdk = AsyncHASDK(mqtt_settings=mqtt_config)
    assert sdk._mqtt is not None


# ── lines 58-59: start() ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_calls_mqtt_connect():
    manager = MagicMock()
    sdk = make_sdk(manager)
    sdk._mqtt = AsyncMock()

    await sdk.start()

    sdk._mqtt.connect.assert_awaited_once()


# ── lines 71-72: shutdown() ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_shutdown_calls_mqtt_disconnect():
    manager = MagicMock()
    sdk = make_sdk(manager)
    sdk._mqtt = AsyncMock()

    await sdk.shutdown()

    sdk._mqtt.disconnect.assert_awaited_once()


# ── lines 78-79: register() happy path ───────────────────────────────────────

@pytest.mark.asyncio
async def test_register_valid_entity():
    manager = MagicMock()
    manager.register = AsyncMock()
    sdk = make_sdk(manager)
    entity = make_entity()

    await sdk.register(entity)

    manager.register.assert_awaited_once_with(entity, None)


@pytest.mark.asyncio
async def test_register_with_callback():
    manager = MagicMock()
    manager.register = AsyncMock()
    sdk = make_sdk(manager)
    entity = make_entity()

    async def cb(topic: str, payload: str) -> None:
        pass

    await sdk.register(entity, cb)

    manager.register.assert_awaited_once_with(entity, cb)


# ── line 93: update_state() happy path ───────────────────────────────────────

@pytest.mark.asyncio
async def test_update_state_valid_entity():
    manager = MagicMock()
    manager.update_state = AsyncMock()
    sdk = make_sdk(manager)
    entity = make_entity()

    await sdk.update_state(entity, "ON")

    manager.update_state.assert_awaited_once_with(entity, "ON")


# ── lines 105 + 119-122: on_command() ────────────────────────────────────────

@pytest.mark.asyncio
async def test_on_command_valid():
    manager = MagicMock()
    manager.set_command_callback = AsyncMock()
    sdk = make_sdk(manager)
    entity = make_entity()

    async def cb(topic: str, payload: str) -> None:
        pass

    await sdk.on_command(entity, cb)

    manager.set_command_callback.assert_awaited_once_with(entity, cb)


@pytest.mark.asyncio
async def test_on_command_non_callable_raises():
    manager = MagicMock()
    sdk = make_sdk(manager)
    entity = make_entity()

    with pytest.raises(SDKError):
        await sdk.on_command(entity, "not_a_callable")  # type: ignore[arg-type]


# ── line 133: create_entity() ─────────────────────────────────────────────────

def test_create_entity_delegates_to_manager():
    manager = MagicMock()
    expected = make_entity()
    manager.create_entity.return_value = expected
    sdk = make_sdk(manager)

    result = sdk.create_entity(
        domain=HADomain.SWITCH,
        name="Relay",
        unique_id="relay_1",
    )

    manager.create_entity.assert_called_once_with(
        domain=HADomain.SWITCH,
        name="Relay",
        unique_id="relay_1",
        device_info=None,
        extra=None,
    )
    assert result is expected


# ── line 145: unregister() ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_unregister_delegates_to_manager():
    manager = MagicMock()
    manager.unregister = AsyncMock()
    sdk = make_sdk(manager)
    entity = make_entity()

    await sdk.unregister(entity)

    manager.unregister.assert_awaited_once_with(entity)


# ── line 151: is_registered() ─────────────────────────────────────────────────

def test_is_registered_true():
    manager = MagicMock()
    manager.is_registered.return_value = True
    sdk = make_sdk(manager)
    entity = make_entity()

    assert sdk.is_registered(entity) is True
    manager.is_registered.assert_called_once_with(entity)


def test_is_registered_false():
    manager = MagicMock()
    manager.is_registered.return_value = False
    sdk = make_sdk(manager)
    entity = make_entity()

    assert sdk.is_registered(entity) is False               
