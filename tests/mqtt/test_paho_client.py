import json
from unittest.mock import MagicMock, patch

import pytest

from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.exceptions import MQTTError, ValidationError
from ha_mqtt_sdk.mqtt.paho_client import PahoMQTTClient

# -----------------------------
# Helpers
# -----------------------------


@pytest.fixture
def config():
    return MQTTSettings(
        host="localhost",
        port=1883,
        keepalive=60,
        client_id="test-client",
        reconnect=True,
        reconnect_delay_min=0.1,
        reconnect_delay_max=1,
        username=None,
        password=None,
        tls=False,
    )


@pytest.fixture
def mqtt_client(config):
    with patch("ha_mqtt_sdk.mqtt.paho_client.mqtt.Client") as mock_client:
        instance = MagicMock()
        mock_client.return_value = instance

        client = PahoMQTTClient(config)
        return client, instance


# -----------------------------
# connect / disconnect
# -----------------------------


def test_connect_sets_connection(mqtt_client):
    client, instance = mqtt_client

    client.connect()

    instance.connect.assert_called_once()
    instance.loop_start.assert_called_once()


def test_disconnect_graceful(mqtt_client):
    client, instance = mqtt_client

    client.connect()
    client.disconnect()

    instance.disconnect.assert_called_once()
    instance.loop_stop.assert_called_once()


# -----------------------------
# publish
# -----------------------------


def test_publish_success(mqtt_client):
    client, instance = mqtt_client

    client._connected = True

    client.publish("topic/test", {"a": 1})

    instance.publish.assert_called_once()
    args = instance.publish.call_args[0]

    assert args[0] == "topic/test"
    assert '"a": 1' in args[1]


def test_publish_not_connected():
    config = MQTTSettings(
        host="localhost",
        port=1883,
        keepalive=60,
        client_id="test",
        reconnect=True,
        reconnect_delay_min=0.1,
        reconnect_delay_max=1,
        username=None,
        password=None,
        tls=False,
    )

    with patch("ha_mqtt_sdk.mqtt.paho_client.mqtt.Client"):
        client = PahoMQTTClient(config)

        with pytest.raises(MQTTError):
            client.publish("topic", "data")


def test_publish_empty_topic(mqtt_client):
    client, _ = mqtt_client
    client._connected = True

    with pytest.raises(ValidationError):
        client.publish("", "data")


# -----------------------------
# subscribe
# -----------------------------


def test_subscribe_stores_topic(mqtt_client):
    client, instance = mqtt_client

    client.subscribe("home/test")

    assert "home/test" in client._subscriptions


def test_subscribe_calls_mqtt_when_connected(mqtt_client):
    client, instance = mqtt_client
    client._connected = True

    client.subscribe("home/test")

    instance.subscribe.assert_called_with("home/test")


# -----------------------------
# LWT
# -----------------------------


def test_set_last_will(mqtt_client):
    client, instance = mqtt_client

    client.set_last_will("home/status", "offline")

    instance.will_set.assert_called_once_with(
        "home/status",
        payload="offline",
        retain=True,
    )


# -----------------------------
# on_message callback
# -----------------------------


def test_on_message_calls_callback(mqtt_client):
    client, _ = mqtt_client

    callback = MagicMock()
    client.set_message_callback(callback)

    msg = MagicMock()
    msg.topic = "test/topic"
    msg.payload = b"hello"

    client._on_message(None, None, msg)

    callback.assert_called_once_with("test/topic", "hello")


# -----------------------------
# on_connect
# -----------------------------


def test_on_connect_success(mqtt_client):
    client, instance = mqtt_client

    client.subscribe("t1")
    client.subscribe("t2")

    client._on_connect(None, None, None, 0)

    assert client._connected is True
    instance.subscribe.assert_any_call("t1")
    instance.subscribe.assert_any_call("t2")


def test_on_connect_failure_logs(mqtt_client):
    client, _ = mqtt_client

    client._on_connect(None, None, None, 1)

    assert client._connected is False


# -----------------------------
# on_disconnect
# -----------------------------


def test_on_disconnect_sets_state(mqtt_client):
    client, _ = mqtt_client

    client._on_disconnect(None, None, 0)

    assert client._connected is False


def test_reconnect_thread_starts(mqtt_client):
    client, instance = mqtt_client

    client._connected = False
    client._config.reconnect = True

    client._on_disconnect(None, None, 1)

    # thread moet bestaan
    assert client._reconnect_thread is not None
    assert client._reconnect_thread.is_alive()


def test_reconnect_thread_not_started_twice(mqtt_client):
    client, _ = mqtt_client

    client._connected = False
    client._config.reconnect = True

    client._ensure_reconnect_thread()
    first = client._reconnect_thread

    client._ensure_reconnect_thread()

    assert client._reconnect_thread is first


def test_message_callback_exception_handled(mqtt_client):
    client, _ = mqtt_client

    def bad_callback(topic, payload):
        raise ValueError("boom")

    client.set_message_callback(bad_callback)

    msg = MagicMock()
    msg.topic = "t"
    msg.payload = b"data"

    # mag niet crashen
    client._on_message(None, None, msg)


def test_publish_mqtt_exception(mqtt_client):
    client, instance = mqtt_client
    client._connected = True

    instance.publish.side_effect = Exception("fail")

    with pytest.raises(MQTTError):
        client.publish("t", "data")


def test_connect_failure_raises_error():
    config = MQTTSettings(
        host="bad",
        port=1883,
        keepalive=60,
        client_id="x",
        reconnect=True,
        reconnect_delay_min=0.1,
        reconnect_delay_max=1,
        username=None,
        password=None,
        tls=False,
    )

    with patch("ha_mqtt_sdk.mqtt.paho_client.mqtt.Client") as mock:
        instance = MagicMock()
        instance.connect.side_effect = Exception("fail")
        mock.return_value = instance

        client = PahoMQTTClient(config)

        with pytest.raises(MQTTError):
            client.connect()


def test_disconnect_when_already_shutdown(mqtt_client):
    client, instance = mqtt_client

    client._shutdown = True

    client.disconnect()

    instance.disconnect.assert_not_called()


@patch("time.sleep", return_value=None)
def test_reconnect_loop_exits_when_shutdown(mock_sleep, mqtt_client):
    client, instance = mqtt_client

    client._shutdown = True

    client._reconnect_loop()

    # mag gewoon stoppen zonder crash
    assert True


def test_reconnect_thread_already_running_skips_creation(mqtt_client):
    client, _ = mqtt_client

    mock_thread = MagicMock()
    mock_thread.is_alive.return_value = True

    client._reconnect_thread = mock_thread

    client._ensure_reconnect_thread()

    # moet NIET vervangen worden
    assert client._reconnect_thread is mock_thread


def test_message_callback_exception_path(mqtt_client):
    client, _ = mqtt_client

    def bad_callback(topic, payload):
        raise RuntimeError("boom")

    client.set_message_callback(bad_callback)

    msg = MagicMock()
    msg.topic = "t"
    msg.payload = b"123"

    client._on_message(None, None, msg)

    # als het goed is: geen crash


def test_reconnect_loop_exits_when_connected(mqtt_client):
    client, _ = mqtt_client

    client._shutdown = False
    client._connected = True

    with patch("time.sleep"):
        client._reconnect_loop()

    assert True


def test_reconnect_success_exits_loop(mqtt_client):
    client, instance = mqtt_client

    instance.reconnect.return_value = True

    client._shutdown = False
    client._connected = False

    client._reconnect_loop()

    instance.reconnect.assert_called_once()


def test_reconnect_thread_already_running_branch(mqtt_client):
    client, _ = mqtt_client

    thread = MagicMock()
    thread.is_alive.return_value = True

    client._reconnect_thread = thread

    # eerste call zet thread misschien niet goed
    client._ensure_reconnect_thread()

    # tweede call moet return branch triggeren
    client._ensure_reconnect_thread()


def test_message_callback_exception_branch(mqtt_client):
    client, _ = mqtt_client

    def bad(topic, payload):
        raise ValueError("boom")

    client.set_message_callback(bad)

    msg = MagicMock()
    msg.topic = "t"
    msg.payload = b"123"

    client._on_message(None, None, msg)


def test_reconnect_loop_condition_branch(mqtt_client):
    client, instance = mqtt_client

    client._shutdown = False
    client._connected = False

    instance.reconnect.return_value = None

    with patch("time.sleep", return_value=None):
        client._reconnect_loop()


def test_reconnect_success_exit_path(mqtt_client):
    client, instance = mqtt_client

    instance.reconnect.return_value = True

    client._shutdown = False
    client._connected = False

    client._reconnect_loop()

    instance.reconnect.assert_called_once()


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
def mqtt_client_2(mqtt_settings):
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


def test_set_last_will_2(mqtt_client):
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


def test_subscribe_stores_topic_2(mqtt_client):
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


def test_on_connect_success_2(mqtt_client):
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


def test_on_disconnect_starts_reconnect_thread(
    mqtt_client,
):
    mqtt_client._shutdown = False
    mqtt_client._config.reconnect = True

    mqtt_client._ensure_reconnect_thread = MagicMock()

    mqtt_client._on_disconnect(None, None, 1)

    mqtt_client._ensure_reconnect_thread.assert_called_once()


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
