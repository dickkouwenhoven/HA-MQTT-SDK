import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ha_mqtt_sdk.exceptions import MQTTError
from ha_mqtt_sdk.mqtt.async_client import AsyncMQTTClient

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


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
# Helpers
# ------------------------------------------------------------------


class FailOnceMessageIterator:
    """Yields one RuntimeError then stops — used to trigger reconnect logic."""

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise RuntimeError("connection lost")


class CancelledMessageIterator:
    """Immediately raises CancelledError — simulates task cancellation."""

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise asyncio.CancelledError


class SingleMessageIterator:
    """Yields one message then stops."""

    def __init__(self, topic: str, payload: bytes):
        self._message = MagicMock()
        self._message.topic = topic
        self._message.payload = payload
        self._done = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._done:
            raise StopAsyncIteration
        self._done = True
        return self._message


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
    ) as mock_start:
        await mqtt_client.connect()

        mock_start.assert_awaited_once()
        assert mqtt_client._shutdown is False


@pytest.mark.asyncio
async def test_connect_when_already_connected(mqtt_client):
    """Already-running listen task: _start_connection must not be called."""
    mqtt_client._listen_task = MagicMock()
    mqtt_client._listen_task.done.return_value = False

    with patch.object(mqtt_client, "_start_connection", AsyncMock()) as mock_start:
        await mqtt_client.connect()

    mock_start.assert_not_awaited()


# ------------------------------------------------------------------
# Start connection
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_connection(mqtt_client, mock_aiomqtt_client):
    await mqtt_client._start_connection()

    mock_aiomqtt_client.__aenter__.assert_awaited_once()

    assert mqtt_client._listen_task is not None


@pytest.mark.asyncio
async def test_start_connection_with_lwt(mqtt_client):
    """LWT configured: aiomqtt. Will must be passed to the client constructor."""
    mqtt_client.set_last_will("device/availability", "offline")

    with patch("ha_mqtt_sdk.mqtt.async_client.aiomqtt.Client") as client_cls:
        client_instance = AsyncMock()
        client_instance.__aenter__ = AsyncMock(return_value=client_instance)
        client_cls.return_value = client_instance

        await mqtt_client._start_connection()

        _, kwargs = client_cls.call_args
        assert kwargs["will"] is not None


@pytest.mark.asyncio
async def test_start_connection_closes_existing_client(mqtt_client, mock_aiomqtt_client):
    """Lines 87-88: existing client must be closed before reconnecting."""
    existing_client = AsyncMock()
    existing_client.__aexit__ = AsyncMock(return_value=None)
    mqtt_client._client = existing_client

    with patch(
        "ha_mqtt_sdk.mqtt.async_client.aiomqtt.Client",
        return_value=mock_aiomqtt_client,
    ):
        await mqtt_client._start_connection()

    existing_client.__aexit__.assert_awaited_once_with(None, None, None)


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


@pytest.mark.asyncio
async def test_disconnect_when_already_shutdown(mqtt_client):
    """Line 105: second disconnect call must be a no-op."""
    mqtt_client._shutdown = True
    mqtt_client._mqtt = MagicMock()

    await mqtt_client.disconnect()  # must not raise

    assert mqtt_client._shutdown is True


@pytest.mark.asyncio
async def test_disconnect_cancels_reconnect_task(mqtt_client):
    async def dummy():
        await asyncio.sleep(3600)

    mqtt_client._reconnect_task = asyncio.create_task(dummy())

    await mqtt_client.disconnect()

    assert mqtt_client._reconnect_task is None


# --------------------------------------------------
# Publish
# --------------------------------------------------


@pytest.mark.asyncio
async def test_publish_string(mqtt_client, mock_aiomqtt_client):
    mqtt_client._client = mock_aiomqtt_client

    await mqtt_client.publish("test/topic", "ON")

    mock_aiomqtt_client.publish.assert_awaited_once_with(
        "test/topic",
        "ON",
        retain=False,
    )


@pytest.mark.asyncio
async def test_publish_dict_serializes_to_json(mqtt_client, mock_aiomqtt_client):
    mqtt_client._client = mock_aiomqtt_client

    payload = {"state": "ON"}

    await mqtt_client.publish("test/topic", payload)

    mock_aiomqtt_client.publish.assert_awaited_once_with(
        "test/topic",
        json.dumps(payload),
        retain=False,
    )


@pytest.mark.asyncio
async def test_publish_without_connection(mqtt_client):
    with pytest.raises(MQTTError):
        await mqtt_client.publish("topic", "payload")


@pytest.mark.asyncio
async def test_publish_wraps_exception(mqtt_client, mock_aiomqtt_client):
    mqtt_client._client = mock_aiomqtt_client
    mock_aiomqtt_client.publish.side_effect = RuntimeError("boom")

    with pytest.raises(MQTTError):
        await mqtt_client.publish("test/topic", "ON")


# --------------------------------------------------
# Subscribe
# --------------------------------------------------


@pytest.mark.asyncio
async def test_subscribe(mqtt_client, mock_aiomqtt_client):
    mqtt_client._client = mock_aiomqtt_client

    await mqtt_client.subscribe("test/topic")

    mock_aiomqtt_client.subscribe.assert_awaited_once_with("test/topic")


@pytest.mark.asyncio
async def test_subscribe_stores_topic(mqtt_client, mock_aiomqtt_client):
    mqtt_client._client = mock_aiomqtt_client

    await mqtt_client.subscribe("test/topic")

    assert "test/topic" in mqtt_client._subscriptions


@pytest.mark.asyncio
async def test_subscribe_without_connection(mqtt_client):
    with pytest.raises(MQTTError):
        await mqtt_client.subscribe("test/topic")


# --------------------------------------------------
# Set_message_callback
# --------------------------------------------------


def test_set_message_callback(mqtt_client):
    callback = AsyncMock()

    mqtt_client.set_message_callback(callback)

    assert mqtt_client._message_callback == callback


# --------------------------------------------------
# Listen
# --------------------------------------------------


@pytest.mark.asyncio
async def test_listen_cancelled(mqtt_client):
    """CancelledError must propagate, not be swallowed."""
    mqtt_client._client = MagicMock()

    mqtt_client._client.messages = CancelledMessageIterator()

    with pytest.raises(asyncio.CancelledError):
        await mqtt_client._listen()


@pytest.mark.asyncio
async def test_listen_routes_message_to_callback(mqtt_client):
    """Lines 173-183: incoming message must be dispatched to the callback."""
    callback = AsyncMock()
    mqtt_client.set_message_callback(callback)
    mqtt_client._client = MagicMock()
    mqtt_client._client.messages = SingleMessageIterator("home/sensor", b"ON")

    await mqtt_client._listen()

    callback.assert_awaited_once_with("home/sensor", "ON")


@pytest.mark.asyncio
async def test_listen_callback_exception_is_logged(mqtt_client):
    """Lines 179-183: callback error must be caught and logged, not propagated."""

    async def bad_callback(topic: str, payload: str) -> None:
        raise RuntimeError("callback failure")

    mqtt_client.set_message_callback(bad_callback)
    mqtt_client._client = MagicMock()
    mqtt_client._client.messages = SingleMessageIterator("home/sensor", b"ON")

    await mqtt_client._listen()  # must not raise


@pytest.mark.asyncio
async def test_listen_starts_reconnect_on_error(mqtt_client):
    """Line 195-198: unexpected disconnect must schedule a reconnect task."""
    mqtt_client._shutdown = False
    mqtt_client._config.reconnect = True

    mqtt_client._client = MagicMock()
    mqtt_client._client.messages = FailOnceMessageIterator()

    await mqtt_client._listen()

    assert mqtt_client._reconnect_task is not None


@pytest.mark.asyncio
async def test_listen_no_reconnect_when_shutdown(mqtt_client):
    """Line 190: no reconnect task when shutdown is True."""
    mqtt_client._shutdown = True
    mqtt_client._config.reconnect = True
    mqtt_client._client = MagicMock()
    mqtt_client._client.messages = FailOnceMessageIterator()

    await mqtt_client._listen()

    assert mqtt_client._reconnect_task is None


@pytest.mark.asyncio
async def test_listen_no_reconnect_when_disabled(mqtt_client):
    """Line 193: no reconnect task when reconnect config is False."""
    mqtt_client._shutdown = False
    mqtt_client._config.reconnect = False
    mqtt_client._client = MagicMock()
    mqtt_client._client.messages = FailOnceMessageIterator()

    await mqtt_client._listen()

    assert mqtt_client._reconnect_task is None


@pytest.mark.asyncio
async def test_listen_no_callback_registered(mqtt_client):
    """Lines 178-172: message received but no callback set — must not raise."""
    mqtt_client._message_callback = None
    mqtt_client._client = MagicMock()
    mqtt_client._client.messages = SingleMessageIterator("home/sensor", b"ON")

    await mqtt_client._listen()  # must complete without error


@pytest.mark.asyncio
async def test_listen_skips_reconnect_if_task_already_running(mqtt_client):
    """Line 195->exit: existing reconnect task that is not done must not be replaced."""
    mqtt_client._shutdown = False
    mqtt_client._config.reconnect = True
    mqtt_client._client = MagicMock()
    mqtt_client._client.messages = FailOnceMessageIterator()

    existing_task = MagicMock()
    existing_task.done.return_value = False
    mqtt_client._reconnect_task = existing_task

    await mqtt_client._listen()

    assert mqtt_client._reconnect_task is existing_task


# --------------------------------------------------
# Reconnect
# --------------------------------------------------


@pytest.mark.asyncio
async def test_reconnect_loop_resubscribes(mqtt_client):
    mqtt_client._subscriptions = {
        "topic/1",
        "topic/2",
    }

    mqtt_client._client = AsyncMock()

    async def start_connection():
        mqtt_client._shutdown = True

    with patch.object(
        mqtt_client,
        "_start_connection",
        side_effect=start_connection,
    ):
        mqtt_client._shutdown = False

        await mqtt_client._reconnect_loop()

    mqtt_client._client.subscribe.assert_any_await("topic/1")
    mqtt_client._client.subscribe.assert_any_await("topic/2")


@pytest.mark.asyncio
async def test_reconnect_loop_backoff(mqtt_client):
    """Line 230: delay must double after each failed attempt."""
    call_count = 0

    async def start_connection():
        nonlocal call_count

        call_count += 1

        if call_count == 1:
            raise RuntimeError("boom")

        mqtt_client._shutdown = True

    with (
        patch.object(
            mqtt_client,
            "_start_connection",
            side_effect=start_connection,
        ),
        patch(
            "ha_mqtt_sdk.mqtt.async_client.asyncio.sleep",
            AsyncMock(),
        ),
    ):
        await mqtt_client._reconnect_loop()

    assert call_count == 2


@pytest.mark.asyncio
async def test_reconnect_loop_cancelled(mqtt_client):
    """Lines 226-227: CancelledError inside reconnect must propagate."""

    async def start_connection():
        raise asyncio.CancelledError

    with (
        patch.object(mqtt_client, "_start_connection", side_effect=start_connection),
        patch("ha_mqtt_sdk.mqtt.async_client.asyncio.sleep", AsyncMock()),
        pytest.raises(asyncio.CancelledError),
    ):
        await mqtt_client._reconnect_loop()


@pytest.mark.asyncio
async def test_reconnect_loop_exits_immediately_when_shutdown(mqtt_client):
    """Line 207->exit: loop must not iterate if shutdown is already True."""
    mqtt_client._shutdown = True

    with patch("ha_mqtt_sdk.mqtt.async_client.asyncio.sleep", AsyncMock()) as mock_sleep:
        await mqtt_client._reconnect_loop()

    mock_sleep.assert_not_awaited()


# --------------------------------------------------
# _clear_reconnect_task
# --------------------------------------------------


def test_clear_reconnect_task_clears_matching_task(mqtt_client):
    """Lines 237-238: callback clears only if task matches."""
    task = MagicMock()
    mqtt_client._reconnect_task = task

    mqtt_client._clear_reconnect_task(task)

    assert mqtt_client._reconnect_task is None


def test_clear_reconnect_task_ignores_other_task(mqtt_client):
    """Line 237->exit: different task must not clear _reconnect_task."""
    task_a = MagicMock()
    task_b = MagicMock()
    mqtt_client._reconnect_task = task_a

    mqtt_client._clear_reconnect_task(task_b)

    assert mqtt_client._reconnect_task is task_a


def test_ensure_reconnect_task_creates_task(mqtt_client):
    """Lines 233-234: must create a new task when none exists."""
    mqtt_client._reconnect_task = None

    with patch(
        "ha_mqtt_sdk.mqtt.async_client.asyncio.create_task", return_value=MagicMock()
    ) as mock_create:
        mqtt_client._ensure_reconnect_task()

    mock_create.assert_called_once()


def test_ensure_reconnect_task_skips_if_task_running(mqtt_client):
    """Line 233->exit: existing running task must not be replaced."""
    existing_task = MagicMock()
    existing_task.done.return_value = False
    mqtt_client._reconnect_task = existing_task

    with (
        patch.object(mqtt_client, "_reconnect_loop", AsyncMock()),
        patch(
            "ha_mqtt_sdk.mqtt.async_client.asyncio.create_task",
            return_value=MagicMock(),
        ) as mock_create,
    ):
        mqtt_client._ensure_reconnect_task()

    mock_create.assert_not_called()
    assert mqtt_client._reconnect_task is existing_task
