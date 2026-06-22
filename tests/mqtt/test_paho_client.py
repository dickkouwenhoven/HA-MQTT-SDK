from unittest.mock import MagicMock, patch

import json
import pytest
import threading

from ha_mqtt_sdk.exceptions import MQTTError, ValidationError
from ha_mqtt_sdk.mqtt.paho_client import PahoMQTTClient

# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------


@pytest.fixture
def mqtt_settings():
    config = MagicMock()
    config.client_id = "test-client"
    config.host = "localhost"
    config.port = 1883
    config.keepalive = 60
    config.username = None
    config.password = None
    config.tls = False
    config.reconnect = True
    config.reconnect_delay_min = 1
    config.reconnect_delay_max = 8
    return config


@pytest.fixture
def mock_paho():
    with patch("ha_mqtt_sdk.mqtt.paho_client.mqtt.Client") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        yield instance


@pytest.fixture
def mqtt_client(mqtt_settings, mock_paho):
    return PahoMQTTClient(mqtt_settings)


# ── helpers ───────────────────────────────────────────────────────────────────


def make_message(topic: str, payload: bytes) -> MagicMock:
    msg = MagicMock()
    msg.topic = topic
    msg.payload.decode.return_value = payload.decode()
    return msg


# ── constructor ───────────────────────────────────────────────────────────────


def test_init_registers_callbacks(mqtt_client):
    assert mqtt_client._client.on_connect == mqtt_client._on_connect
    assert mqtt_client._client.on_disconnect == mqtt_client._on_disconnect
    assert mqtt_client._client.on_message == mqtt_client._on_message


def test_init_with_username_calls_auth(mqtt_settings, mock_paho):
    """Line 47: username_pw_set must be called when credentials are provided."""
    mqtt_settings.username = "user"
    mqtt_settings.password = "pass"

    PahoMQTTClient(mqtt_settings)

    mock_paho.username_pw_set.assert_called_once_with("user", "pass")


def test_init_with_tls_calls_tls_set(mqtt_settings, mock_paho):
    """Line 50: tls_set must be called when TLS is enabled."""
    mqtt_settings.tls = True

    PahoMQTTClient(mqtt_settings)

    mock_paho.tls_set.assert_called_once()


# ── last will ─────────────────────────────────────────────────────────────────


def test_set_last_will(mqtt_client):
    mqtt_client.set_last_will("device/status", "offline")

    mqtt_client._client.will_set.assert_called_once_with(
        "device/status", payload="offline", retain=True
    )


def test_set_last_will_default_payload(mqtt_client):
    mqtt_client.set_last_will("device/status")

    mqtt_client._client.will_set.assert_called_once_with(
        "device/status", payload="offline", retain=True
    )


# ── connect ───────────────────────────────────────────────────────────────────


def test_connect(mqtt_client, mqtt_settings):
    mqtt_client.connect()

    mqtt_client._client.connect.assert_called_once_with(
        mqtt_settings.host, mqtt_settings.port, mqtt_settings.keepalive
    )
    mqtt_client._client.loop_start.assert_called_once()


def test_connect_when_already_connected(mqtt_client):
    """Lines 90-91: second connect call must be a no-op."""
    mqtt_client._connected = True

    mqtt_client.connect()

    mqtt_client._client.connect.assert_not_called()


def test_connect_failure_raises_mqtt_error(mqtt_settings, mock_paho):
    mock_paho.connect.side_effect = Exception("refused")
    client = PahoMQTTClient(mqtt_settings)

    with pytest.raises(MQTTError):
        client.connect()


# ── disconnect ────────────────────────────────────────────────────────────────


def test_disconnect(mqtt_client):
    mqtt_client.disconnect()

    assert mqtt_client._shutdown is True
    mqtt_client._client.disconnect.assert_called_once()
    mqtt_client._client.loop_stop.assert_called_once()


def test_disconnect_when_already_shutdown(mqtt_client):
    mqtt_client._shutdown = True

    mqtt_client.disconnect()

    mqtt_client._client.disconnect.assert_not_called()


# ── publish ───────────────────────────────────────────────────────────────────


def test_publish_string(mqtt_client):
    mqtt_client._connected = True

    mqtt_client.publish("test/topic", "ON")

    mqtt_client._client.publish.assert_called_once_with("test/topic", "ON", retain=False)


def test_publish_dict_serializes_to_json(mqtt_client):
    mqtt_client._connected = True
    payload = {"state": "ON"}

    mqtt_client.publish("test/topic", payload)

    mqtt_client._client.publish.assert_called_once_with(
        "test/topic", json.dumps(payload), retain=False
    )


def test_publish_with_retain(mqtt_client):
    mqtt_client._connected = True

    mqtt_client.publish("test/topic", "ON", retain=True)

    mqtt_client._client.publish.assert_called_once_with("test/topic", "ON", retain=True)


def test_publish_empty_topic_raises(mqtt_client):
    mqtt_client._connected = True

    with pytest.raises(ValidationError):
        mqtt_client.publish("", "payload")


def test_publish_not_connected_raises(mqtt_client):
    with pytest.raises(MQTTError):
        mqtt_client.publish("topic", "data")


def test_publish_wraps_mqtt_exception(mqtt_client):
    mqtt_client._connected = True
    mqtt_client._client.publish.side_effect = Exception("fail")

    with pytest.raises(MQTTError):
        mqtt_client.publish("topic", "data")


# ── subscribe ─────────────────────────────────────────────────────────────────


def test_subscribe_stores_topic(mqtt_client):
    mqtt_client.subscribe("home/test")

    assert "home/test" in mqtt_client._subscriptions


def test_subscribe_calls_mqtt_when_connected(mqtt_client):
    mqtt_client._connected = True

    mqtt_client.subscribe("home/test")

    mqtt_client._client.subscribe.assert_called_with("home/test")


def test_subscribe_does_not_call_mqtt_when_disconnected(mqtt_client):
    mqtt_client._connected = False

    mqtt_client.subscribe("home/test")

    mqtt_client._client.subscribe.assert_not_called()


def test_subscribe_empty_topic_raises(mqtt_client):
    with pytest.raises(MQTTError):
        mqtt_client.subscribe("")


# ── set_message_callback ──────────────────────────────────────────────────────


def test_set_message_callback(mqtt_client):
    callback = MagicMock()

    mqtt_client.set_message_callback(callback)

    assert mqtt_client._message_callback == callback


# ── _on_message ───────────────────────────────────────────────────────────────


def test_on_message_dispatches_to_callback(mqtt_client):
    callback = MagicMock()
    mqtt_client.set_message_callback(callback)

    mqtt_client._on_message(None, None, make_message("test/topic", b"hello"))

    callback.assert_called_once_with("test/topic", "hello")


def test_on_message_without_callback(mqtt_client):
    mqtt_client._on_message(None, None, make_message("test/topic", b"hello"))


def test_on_message_callback_exception_is_caught(mqtt_client):
    def bad_callback(topic: str, payload: str) -> None:
        raise RuntimeError("boom")

    mqtt_client.set_message_callback(bad_callback)

    mqtt_client._on_message(None, None, make_message("t", b"data"))  # must not raise


# ── _on_connect ───────────────────────────────────────────────────────────────


def test_on_connect_success(mqtt_client):
    mqtt_client.subscribe("t1")
    mqtt_client.subscribe("t2")

    mqtt_client._on_connect(None, None, None, 0)

    assert mqtt_client._connected is True
    mqtt_client._client.subscribe.assert_any_call("t1")
    mqtt_client._client.subscribe.assert_any_call("t2")


def test_on_connect_resubscribe_exception_is_caught(mqtt_client):
    """Lines 177-178: subscribe failure during reconnect must be caught and logged."""
    mqtt_client._subscriptions = {"test/topic"}
    mqtt_client._client.subscribe.side_effect = Exception("sub failed")

    mqtt_client._on_connect(None, None, None, 0)  # must not raise

    assert mqtt_client._connected is True


def test_on_connect_failure(mqtt_client):
    mqtt_client._on_connect(None, None, None, 1)

    assert mqtt_client._connected is False


# ── _on_disconnect ────────────────────────────────────────────────────────────


def test_on_disconnect_sets_connected_false(mqtt_client):
    mqtt_client._connected = True

    mqtt_client._on_disconnect(None, None, 0)

    assert mqtt_client._connected is False


def test_on_disconnect_intentional_skips_reconnect(mqtt_client):
    mqtt_client._shutdown = True
    mqtt_client._ensure_reconnect_thread = MagicMock()

    mqtt_client._on_disconnect(None, None, 0)

    mqtt_client._ensure_reconnect_thread.assert_not_called()


def test_on_disconnect_starts_reconnect_thread(mqtt_client):
    mqtt_client._shutdown = False
    mqtt_client._config.reconnect = True
    mqtt_client._ensure_reconnect_thread = MagicMock()

    mqtt_client._on_disconnect(None, None, 1)

    mqtt_client._ensure_reconnect_thread.assert_called_once()


def test_on_disconnect_no_reconnect_when_disabled(mqtt_client):
    """Line 197->exit: reconnect thread must not start when reconnect=False."""
    mqtt_client._shutdown = False
    mqtt_client._config.reconnect = False
    mqtt_client._ensure_reconnect_thread = MagicMock()

    mqtt_client._on_disconnect(None, None, 1)

    mqtt_client._ensure_reconnect_thread.assert_not_called()


# ── _ensure_reconnect_thread ──────────────────────────────────────────────────


def test_ensure_reconnect_thread_creates_thread(mqtt_client):
    mqtt_client._ensure_reconnect_thread()

    assert mqtt_client._reconnect_thread is not None
    assert isinstance(mqtt_client._reconnect_thread, threading.Thread)


def test_ensure_reconnect_thread_skips_if_alive(mqtt_client):
    existing = MagicMock()
    existing.is_alive.return_value = True
    mqtt_client._reconnect_thread = existing

    mqtt_client._ensure_reconnect_thread()

    assert mqtt_client._reconnect_thread is existing


# ── _reconnect_loop ───────────────────────────────────────────────────────────


@patch("ha_mqtt_sdk.mqtt.paho_client.time.sleep")
def test_reconnect_loop_success(mock_sleep, mqtt_client):
    mqtt_client._shutdown = False
    mqtt_client._connected = False

    def reconnect():
        mqtt_client._connected = True

    mqtt_client._client.reconnect.side_effect = reconnect

    mqtt_client._reconnect_loop()

    mqtt_client._client.reconnect.assert_called_once()


@patch("ha_mqtt_sdk.mqtt.paho_client.time.sleep")
def test_reconnect_loop_retries_with_backoff(mock_sleep, mqtt_client):
    mqtt_client._shutdown = False
    mqtt_client._connected = False
    attempts = 0

    def reconnect():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise Exception("boom")
        mqtt_client._connected = True

    mqtt_client._client.reconnect.side_effect = reconnect

    mqtt_client._reconnect_loop()

    assert attempts == 2


@patch("ha_mqtt_sdk.mqtt.paho_client.time.sleep")
def test_reconnect_loop_exits_when_shutdown(mock_sleep, mqtt_client):
    mqtt_client._shutdown = True
    mqtt_client._connected = False

    mqtt_client._reconnect_loop()

    mqtt_client._client.reconnect.assert_not_called()


@patch("ha_mqtt_sdk.mqtt.paho_client.time.sleep")
def test_reconnect_loop_exits_when_already_connected(mock_sleep, mqtt_client):
    mqtt_client._shutdown = False
    mqtt_client._connected = True

    mqtt_client._reconnect_loop()

    mqtt_client._client.reconnect.assert_not_called()
