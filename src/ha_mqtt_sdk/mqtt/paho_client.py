"""
Paho MQTT client implementation (synchronous).

Feature parity with AsyncMQTTClient:
- Exponential reconnect
- Single reconnect thread
- Auto re-subscribe
- LWT support
- Graceful shutdown

Used by:
- HASDK (default MQTT client)
"""

import json
import threading
import time
from collections.abc import Callable
from typing import Any

import paho.mqtt.client as mqtt

from ..config.mqtt import MQTTSettings
from ..exceptions import MQTTError, ValidationError
from ..utils.logger import get_logger
from .base import BaseMQTTClient


class PahoMQTTClient(BaseMQTTClient):
    def __init__(self, config: MQTTSettings):
        self._config = config
        self._logger = get_logger(__name__)

        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=config.client_id,
        )
        self._subscriptions: set[str] = set()
        self._message_callback: Callable | None = None

        self._reconnect_delay = config.reconnect_delay_min
        self._connected = False
        self._shutdown = False

        if config.username:
            self._client.username_pw_set(config.username, config.password)

        if config.tls:
            self._client.tls_set()

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        self._reconnect_thread: threading.Thread | None = None
        self._reconnect_lock = threading.Lock()

        self._lwt_topic: str | None = None
        self._lwt_payload: str = "offline"

    # ---------------------------
    # LWT
    # ---------------------------

    def set_last_will(self, topic: str, payload: str = "offline") -> None:
        """
        Register a Last Will and Testament message.

        Must be called before connect().
        The broker publishes this automatically if the clients disconnects
        ungracefully (crash, power loss, network drop).

        Args:
                topic: Availability topic for the device
                payload: Payload to publish on ungraceful disconnect (default: "offline")
        """
        self._lwt_topic = topic
        self._lwt_payload = payload

        self._client.will_set(topic, payload=payload, retain=True)
        self._logger.debug("Last will set on topic: %s", topic)

    # ----------------------------
    # Connection
    # ----------------------------

    def connect(self) -> None:
        if self._connected:
            self._logger.info("Client already connected to MQTT broke")
            return

        self._logger.info("Connecting to MQTT broker %s:%s", self._config.host, self._config.port)
        self._shutdown = False
        try:
            self._client.connect(
                self._config.host,
                self._config.port,
                self._config.keepalive,
            )

            self._client.loop_start()

        except Exception as e:
            raise MQTTError(f"Failed to connect: {e}") from e

    def disconnect(self) -> None:
        if self._shutdown:
            return

        self._logger.info("Disconnecting MQTT client")
        self._shutdown = True

        try:
            self._client.disconnect()
        finally:
            self._client.loop_stop()

        self._connected = False

    # -----------------------
    # Publish / Subscribe
    # -----------------------
    def publish(self, topic: str, payload: Any, retain: bool = False) -> None:
        if not topic:
            raise ValidationError("Topic must not be empty")

        if not self._connected:
            raise MQTTError("Client is not connected")

        # Avoid double-serializing plain strings (e.g. "ON", "offline")
        message = payload if isinstance(payload, str) else json.dumps(payload)

        self._logger.debug("Publishing to %s: %s", topic, message)

        try:
            self._client.publish(topic, message, retain=retain)
        except Exception as e:
            raise MQTTError(str(e)) from e

    def subscribe(self, topic: str) -> None:
        if not topic:
            raise MQTTError("Topic must not be empty")

        self._subscriptions.add(topic)

        self._logger.debug("Subscribing to topic: %s", topic)

        if self._connected:
            self._client.subscribe(topic)

    def set_message_callback(self, callback: Callable[[str, str], None]) -> None:
        self._message_callback = callback

    # -----------------------
    # Internal callbacks
    # -----------------------

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: object,
        flags: mqtt.ConnectFlags,
        reason_code: mqtt.ReasonCode,
        properties: mqtt.Properties | None = None,
    ) -> None:
        if reason_code == 0:
            self._connected = True
            self._logger.info("Connected to MQTT broker")

            # Re-subscribe after reconnect
            for topic in self._subscriptions:
                try:
                    self._client.subscribe(topic)

                    self._logger.debug("Re-subscribed to topic: %s", topic)
                except Exception as e:
                    self._logger.warning("Failed to re-subscribe %s: %s", topic, e)
        else:
            self._logger.error("Failed to connect, rc=%s", reason_code)

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        reason_code: mqtt.ReasonCode | int | None = None,
        properties: mqtt.Properties | None = None,
    ) -> None:
        self._connected = False

        if self._shutdown:
            self._logger.info("MQTT client disconnected (intentional)")
            return

        self._logger.warning("Unexpected disconnect (rc=%s)", reason_code)

        if self._config.reconnect:
            self._ensure_reconnect_thread()

    def _ensure_reconnect_thread(self) -> None:
        with self._reconnect_lock:
            if self._reconnect_thread and self._reconnect_thread.is_alive():
                return

            self._reconnect_thread = threading.Thread(
                target=self._reconnect_loop,
                daemon=True,
            )

            self._reconnect_thread.start()

    def _reconnect_loop(self) -> None:
        """
        Blocking reconnect loop with exponential backoff.
        Runs in a background daemon thread.
        """

        delay = self._config.reconnect_delay_min

        while not self._shutdown and not self._connected:
            self._logger.info("Reconnecting in %.1fs...", delay)

            time.sleep(delay)

            try:
                self._logger.info("Attempting reconnect...")
                self._client.reconnect()
                self._logger.info("Reconnected successfully")
                return
            except Exception as e:
                self._logger.warning("Reconnect failed: %s", e)
                delay = min(
                    delay * 2,
                    self._config.reconnect_delay_max,
                )

    def _on_message(self, client, userdata, msg) -> None:
        topic = msg.topic
        payload = msg.payload.decode()

        self._logger.debug("Received message on %s: %s", topic, payload)

        if self._message_callback:
            try:
                self._message_callback(topic, payload)
            except Exception as e:
                self._logger.error("Error in message callback for %s: %s", topic, e)
