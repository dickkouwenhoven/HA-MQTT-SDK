import json
from unittest.mock import MagicMock, patch

import pytest

from ha_mqtt_sdk.exceptions import MQTTError, ValidationError
from ha_mqtt_sdk.mqtt.paho_client import PahoMQTTClient


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
def mqtt_client(mqtt_settings):
    with patch("ha_mqtt_sdk.mqtt.paho_client.mqtt.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        client = PahoMQTTClient(mqtt_settings)

        yield client


# ------------------------------------------------------------------
# Constructor
# ------------------------------------------------------------------


def test_init_sets_callbacks(mqtt_client):
    assert mqtt_client._client.on_connect == mqtt_client._on_connect
    assert mqtt_client._client.on_disconnect == mqtt_client._on_disconnect
    assert mqtt_client._client.on_message == mqtt_client._on_message


# ------------------------------------------------------------------
# Last Will
# ------------------------------------------------------------------


def test_set_last_will(mqtt_client):
    mqtt_client.set_last_will("device/status")

    mqtt_client._client.will_set.assert_called_once_with(
        "device/status",
        payload="offline",
        retain=True,
    )


# ------------------------------------------------------------------
# Connect / Disconnect
# ------------------------------------------------------------------


def test_connect(mqtt_client, mqtt_settings):
    mqtt_client.connect()

    mqtt_client._client.connect.assert_called_once_with(
        mqtt_settings.host,
        mqtt_settings.port,
        mqtt_settings.keepalive,
    )

    mqtt_client._client.loop_start.assert_called_once()


def test_disconnect(mqtt_client):
    mqtt_client.disconnect()

    assert mqtt_client._shutdown is True
    mqtt_client._client.loop_stop.assert_called_once()
    mqtt_client._client.disconnect.assert_called_once()


# ------------------------------------------------------------------
# Publish
# ------------------------------------------------------------------


def test_publish_string(mqtt_client):
    mqtt_client._connected = True
    mqtt_client.publish("test/topic", "ON")

    mqtt_client._client.publish.assert_called_once_with(
        "test/topic",
        "ON",
        retain=False,
    )


def test_publish_json_payload(mqtt_client):
    mqtt_client._connected = True
    payload = {"state": "ON"}

    mqtt_client.publish("test/topic", payload)

    mqtt_client._client.publish.assert_called_once_with(
        "test/topic",
        json.dumps(payload),
        retain=False,
    )


def test_publish_with_retain(mqtt_client):
    mqtt_client._connected = True
    mqtt_client.publish("test/topic", "ON", retain=True)

    mqtt_client._client.publish.assert_called_once_with(
        "test/topic",
        "ON",
        retain=True,
    )


def test_publish_empty_topic_raises(mqtt_client):
    with pytest.raises(ValidationError):
        mqtt_client.publish("", "payload")


# ------------------------------------------------------------------
# Subscribe
# ------------------------------------------------------------------


def test_subscribe_stores_topic(mqtt_client):
    mqtt_client.subscribe("test/topic")

    assert "test/topic" in mqtt_client._subscriptions


def test_subscribe_when_connected(mqtt_client):
    mqtt_client._connected = True

    mqtt_client.subscribe("test/topic")

    mqtt_client._client.subscribe.assert_called_once_with("test/topic")


def test_resubscribe_after_connect(mqtt_client):
    mqtt_client.subscribe("test/topic")

    mqtt_client._on_connect(
        None,
        None,
        None,
        0,
    )


def test_subscribe_empty_topic_raises(mqtt_client):
    with pytest.raises(MQTTError):
        mqtt_client.subscribe("")


# ------------------------------------------------------------------
# Message callback
# ------------------------------------------------------------------


def test_message_callback_invoked(mqtt_client):
    callback = MagicMock()

    mqtt_client.set_message_callback(callback)

    msg = MagicMock()
    msg.topic = "sensor/temp"
    msg.payload.decode.return_value = "22.5"

    mqtt_client._on_message(None, None, msg)

    callback.assert_called_once_with(
        "sensor/temp",
        "22.5",
    )


def test_message_callback_not_set(mqtt_client):
    msg = MagicMock()
    msg.topic = "sensor/temp"
    msg.payload.decode.return_value = "22.5"

    mqtt_client._on_message(None, None, msg)

    # Geen exception betekent succes


# ------------------------------------------------------------------
# Connect callback
# ------------------------------------------------------------------


def test_on_connect_success(mqtt_client):
    mqtt_client.subscribe("test/topic")

    mqtt_client._on_connect(None, None, None, 0)

    assert mqtt_client._connected is True

    mqtt_client._client.subscribe.assert_called_once_with("test/topic")


def test_on_connect_failure(mqtt_client):
    mqtt_client._connected = False

    mqtt_client._on_connect(None, None, None, 1)

    assert mqtt_client._connected is False


# ------------------------------------------------------------------
# Disconnect callback
# ------------------------------------------------------------------


def test_on_disconnect_intentional(mqtt_client):
    mqtt_client._shutdown = True

    mqtt_client._on_disconnect(None, None, 0)

    assert mqtt_client._connected is False


@patch("ha_mqtt_sdk.mqtt.paho_client.threading.Thread")
def test_on_disconnect_starts_reconnect_thread(
    mock_thread,
    mqtt_client,
):
    mqtt_client._shutdown = False
    mqtt_client._config.reconnect = True

    mqtt_client._on_disconnect(None, None, 1)

    mock_thread.assert_called_once()


# ------------------------------------------------------------------
# Reconnect loop
# ------------------------------------------------------------------


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
def test_reconnect_loop_retries(mock_sleep, mqtt_client):
    mqtt_client._shutdown = False
    mqtt_client._connected = False

    attempts = 0

    def reconnect_side_effect():
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            raise Exception("boom")

        mqtt_client._connected = True

    mqtt_client._client.reconnect.side_effect = reconnect_side_effect

    mqtt_client._reconnect_loop()

    assert attempts == 2
    assert mqtt_client._client.reconnect.call_count == 2
