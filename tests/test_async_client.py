import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ha_mqtt_sdk.exceptions import MQTTError
from ha_mqtt_sdk.mqtt.async_client import AsyncMQTTClient


@pytest.fixture
def mqtt_settings():
    config = MagicMock()

    config.host = "mqtt"
    config.port = 1883
    config.keepalive = 60

    config.username = None
    config.password = None

    config.reconnect = True
    config.reconnect_delay_min = 1
    config.reconnect_delay_max = 8

    return config


@pytest.fixture
def mock_aiomqtt_client():
    client = AsyncMock()

    client.publish = AsyncMock()
    client.subscribe = AsyncMock()

    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    return client


@pytest.fixture
def mqtt_client(mqtt_settings, mock_aiomqtt_client):
    with patch(
        "ha_mqtt_sdk.mqtt.async_client.aiomqtt.Client",
        return_value=mock_aiomqtt_client,
    ):
        yield AsyncMQTTClient(mqtt_settings)


# ------------------------------------------------------------------
# Last Will
# ------------------------------------------------------------------


def test_set_last_will(mqtt_client):
    mqtt_client.set_last_will("device/status", "offline")

    assert mqtt_client._lwt_topic == "device/status"
    assert mqtt_client._lwt_payload == "offline"


# ------------------------------------------------------------------
# Connect
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connect(mqtt_client):
    with patch.object(
        mqtt_client,
        "_start_connection",
        AsyncMock(),
    ) as start_connection:
        await mqtt_client.connect()

        start_connection.assert_awaited_once()
        assert mqtt_client._shutdown is False


# ------------------------------------------------------------------
# Starct connection
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_connection(
    mqtt_client,
    mock_aiomqtt_client,
):
    with patch("ha_mqtt_sdk.mqtt.async_client.asyncio.create_task") as create_task:
        await mqtt_client._start_connection()

        mock_aiomqtt_client.__aenter__.assert_awaited_once()
        create_task.assert_called_once()


@pytest.mark.asyncio
async def test_start_connection_with_lwt(
    mqtt_client,
):
    mqtt_client.set_last_will(
        "availability",
        "offline",
    )

    async def dummy():
        return None

    dummy_task = asyncio.create_task(dummy())

    with patch("ha_mqtt_sdk.mqtt.async_client.aiomqtt.Client") as client_cls:
        client_instance = AsyncMock()

        client_instance.__aenter__ = AsyncMock(return_value=client_instance)

        client_cls.return_value = client_instance

        with patch(
            "ha_mqtt_sdk.mqtt.async_client.asyncio.create_task",
            return_value=dummy_task,
        ):
            await mqtt_client._start_connection()

        client_cls.assert_called_once()


# ----------------------------------------------------
# Disconnect
# ----------------------------------------------------


@pytest.mark.asyncio
async def test_disconnect(mqtt_client):

    async def dummy():
        await asyncio.sleep(3600)

    task = asyncio.create_task(dummy())

    mqtt_client._listen_task = task
    mqtt_client._client = AsyncMock()

    await mqtt_client.disconnect()

    assert mqtt_client._shutdown is True
    assert task.cancelled()


@pytest.mark.asyncio
async def test_disconnect_without_client(mqtt_client):
    await mqtt_client.disconnect()

    assert mqtt_client._shutdown is True


# --------------------------------------------------
# Publish
# --------------------------------------------------


@pytest.mark.asyncio
async def test_publish_string(
    mqtt_client,
    mock_aiomqtt_client,
):
    mqtt_client._client = mock_aiomqtt_client

    await mqtt_client.publish(
        "test/topic",
        "ON",
    )

    mock_aiomqtt_client.publish.assert_awaited_once_with(
        "test/topic",
        "ON",
        retain=False,
    )


@pytest.mark.asyncio
async def test_publish_json(
    mqtt_client,
    mock_aiomqtt_client,
):
    mqtt_client._client = mock_aiomqtt_client

    payload = {"state": "ON"}

    await mqtt_client.publish(
        "test/topic",
        payload,
    )

    mock_aiomqtt_client.publish.assert_awaited_once_with(
        "test/topic",
        json.dumps(payload),
        retain=False,
    )


@pytest.mark.asyncio
async def test_publish_without_connection(
    mqtt_client,
):
    with pytest.raises(MQTTError):
        await mqtt_client.publish(
            "topic",
            "payload",
        )


# --------------------------------------------------
# Subscribe
# --------------------------------------------------


@pytest.mark.asyncio
async def test_subscribe(
    mqtt_client,
    mock_aiomqtt_client,
):
    mqtt_client._client = mock_aiomqtt_client

    await mqtt_client.subscribe("test/topic")

    mock_aiomqtt_client.subscribe.assert_awaited_once_with("test/topic")


@pytest.mark.asyncio
async def test_subscribe_without_connection(
    mqtt_client,
):
    with pytest.raises(MQTTError):
        await mqtt_client.subscribe("test/topic")


# --------------------------------------------------
# Callback
# --------------------------------------------------


def test_set_message_callback(
    mqtt_client,
):
    callback = AsyncMock()

    mqtt_client.set_message_callback(callback)

    assert mqtt_client._message_callback == callback


# --------------------------------------------------
# Listen
# --------------------------------------------------


@pytest.mark.asyncio
async def test_listen_cancelled(
    mqtt_client,
):
    mqtt_client._client = MagicMock()

    class MessageIterator:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise asyncio.CancelledError

    mqtt_client._client.messages = MessageIterator()

    with pytest.raises(asyncio.CancelledError):
        await mqtt_client._listen()


@pytest.mark.asyncio
async def test_listen_starts_reconnect(
    mqtt_client,
):
    mqtt_client._shutdown = False
    mqtt_client._config.reconnect = True

    mqtt_client._client = MagicMock()

    class MessageIterator:
        def __aiter__(self):
            return self

        async def __anext__(self):
            raise RuntimeError("boom")

    mqtt_client._client.messages = MessageIterator()

    async def dummy():
        return None
        
    dummy_task = asyncio.create_task(dummy())
    
    with patch(
        "ha_mqtt_sdk.mqtt.async_client.asyncio.create_task",
        return_value=dummy_task,
    ):
        await mqtt_client._listen()

    assert mqtt_client._reconnect_task is dummy_task


# --------------------------------------------------
# Reconnect
# --------------------------------------------------


@pytest.mark.asyncio
async def test_reconnect_loop_success(
    mqtt_client,
):
    mqtt_client._callbacks = {
        "topic/1": MagicMock(),
        "topic/2": MagicMock(),
    }

    mqtt_client._client = AsyncMock()

    with patch.object(
        mqtt_client,
        "_start_connection",
        AsyncMock(),
    ) as start_connection:
        mqtt_client._shutdown = False

        await mqtt_client._reconnect_loop()

        start_connection.assert_awaited_once()


@pytest.mark.asyncio
async def test_reconnect_loop_backoff(
    mqtt_client,
):
    call_count = 0

    async def start_connection():
        nonlocal call_count

        call_count += 1

        if call_count == 1:
            raise RuntimeError("boom")

        mqtt_client._shutdown = True

    with patch.object(
        mqtt_client,
        "_start_connection",
        side_effect=start_connection,
    ):
        with patch(
            "ha_mqtt_sdk.mqtt.async_client.asyncio.sleep",
            AsyncMock(),
        ):
            await mqtt_client._reconnect_loop()

    assert call_count == 2
