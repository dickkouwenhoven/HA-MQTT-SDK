"""
Paho MQTT client implementation (synchronous).

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
        self._callbacks: dict[str, Callable] = {}
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
        self._client.will_set(topic, payload=payload, retain=True)
        self._logger.debug("Last will set on topic: %s", topic)

    # ----------------------------
    # Connection
    # ----------------------------

    def connect(self) -> None:
        self._logger.info("Connecting to MQTT broker %s:%s", self._config.host, self._config.port)
        self._shutdown = False
        self._client.connect(
            self._config.host,
            self._config.port,
            self._config.keepalive,
        )

        self._client.loop_start()

    def disconnect(self) -> None:
        self._logger.info("Disconnecting MQTT client")
        self._shutdown = True
        self._client.loop_stop()
        self._client.disconnect()

    # -----------------------
    # Publish / Subscribe
    # -----------------------
    def publish(self, topic: str, payload: Any, retain: bool = False) -> None:
        if not topic:
            raise ValidationError("Topic must not be empty")

        # Avoid double-serializing plain strings (e.g. "ON", "offline")
        message = payload if isinstance(payload, str) else json.dumps(payload)

        self._logger.debug("Publishing to %s: %s", topic, message)

        self._client.publish(topic, message, retain=retain)

    def subscribe(self, topic: str) -> None:
        if not topic:
            raise MQTTError("Topic must not be empty")

        self._client.subscribe(topic)

    def set_message_callback(self, callback: Callable[[str, str], None]) -> None:
        self._message_callback = callback

    # -----------------------
    # Internal callbacks
    # -----------------------

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            self._reconnect_delay = self._config.reconnect_delay_min
            self._logger.info("Connected to MQTT broker")
        else:
            self._logger.error("Failed to connect, rc=%s", rc)

    def _on_disconnect(self, client, userdata, rc) -> None:
        self._connected = False

        if self._shutdown:
            self._logger.info("MQTT client disconnected (intentional)")
            return

        self._logger.warning(
            "Unexpected disconnect (rc=%s). Reconnecting in %.1fs...",
            rc,
            self._reconnect_delay,
        )

        if self._config.reconnect:
            threading.Thread(target=self._reconnect_loop, daemon=True).start()

    def _reconnect_loop(self) -> None:
        """
        Blocking reconnect loop with exponential backoff.
        Runs in a background daemon thread.
        """

        while not self._shutdown and not self._connected:
            time.sleep(self._reconnect_delay)

            try:
                self._logger.info("Attempting reconnect...")
                self._client.reconnect()
                self._logger.info("Reconnected successfully")
                return
            except Exception as e:
                self.logger.warning("Reconnect failed: %s", e)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2,
                    self._config.reconnect_delay_max,
                )

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()

        self._logger.debug("Received message on %s: %s", topic, payload)

        if self._message_callback:
            self._message_callback(topic, payload)
