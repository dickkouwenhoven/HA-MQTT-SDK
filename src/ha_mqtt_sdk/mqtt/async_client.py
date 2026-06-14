"""
Async MQTT client using aiomqtt.

Note: aiomqtt is the actively maintained successor to asyncio-mqtt.
Replace your dependency with: pip install aiomqtt

Used by:
- Advanced users (async path)
"""

import asyncio
import contextlib
import json
from collections.abc import Awaitable, Callable
from typing import Any

import aiomqtt

from ..config.mqtt import MQTTSettings
from ..exceptions import MQTTError
from ..utils.logger import get_logger
from .base_async_mqtt_client import BaseAsyncMQTTClient

MessageCallback = Callable[[str, str], Awaitable[None]]


class AsyncMQTTClient(BaseAsyncMQTTClient):
    def __init__(self, config: MQTTSettings):
        self._config = config
        self._logger = get_logger(__name__)
        self._subscriptions: set[str] = set()
        self._message_callback: Callable | None = None
        self._client: aiomqtt.Client | None = None
        self._listen_task: asyncio.Task | None = None
        self._shutdown = False
        self._lwt_topic: str | None = None
        self._lwt_payload: str = "offline"
        self._reconnect_task: asyncio.Task | None = None
        self._reconnect_lock = asyncio.Lock()

    # -------------------------
    # LWT
    # -------------------------

    def set_last_will(self, topic: str, payload: str = "offline") -> None:
        """
        Register a Last Will and Testament message.

        Must be called before connect().

        Args:
                topic: Availability topic for the device
                payload: Payload published on ungraceful disconnect (default: "offline")
        """
        self._lwt_topic = topic
        self._lwt_payload = payload
        self._logger.debug("Last will configured for topic: %s", topic)

    # -------------------------
    # Connection
    # -------------------------

    async def connect(self) -> None:
        if self._listen_task and not self._listen_task.done():
            self._logger.info("Client already connected with MQTT broker")
            return

        self._logger.info("Connecting (async) to MQTT broker")

        self._shutdown = False
        await self._start_connection()

    async def _start_connection(self) -> None:
        """
        Build the aiomqtt client and start the listener task.
        Extracted so reconnect can call it too.
        """
        will = None
        if self._lwt_topic:
            will = aiomqtt.Will(
                topic=self._lwt_topic,
                payload=self._lwt_payload,
                retain=True,
            )

        if self._client:
            with contextlib.suppress(Exception):
                await self._client.__aexit__(None, None, None)

        self._client = aiomqtt.Client(
            hostname=self._config.host,
            port=self._config.port,
            username=self._config.username,
            password=self._config.password,
            keepalive=self._config.keepalive,
            will=will,
        )

        await self._client.__aenter__()
        self._listen_task = asyncio.create_task(self._listen())
        self._logger.info("Connected (async) to MQTT broker")

    async def disconnect(self) -> None:
        if self._shutdown:
            return

        self._shutdown = True

        if self._reconnect_task:
            self._reconnect_task.cancel()

            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            finally:
                self._reconnect_task = None

        if self._listen_task:
            self._listen_task.cancel()

            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            finally:
                self._listen_task = None

        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None

    # -------------------------
    # Publish / Subscribe
    # -------------------------

    async def publish(self, topic: str, payload: Any, retain: bool = False) -> None:
        if not self._client:
            raise MQTTError("Client is not connected")

        message = payload if isinstance(payload, str) else json.dumps(payload)
        try:
            await self._client.publish(topic, message, retain=retain)
        except Exception as e:
            raise MQTTError(str(e)) from e

    async def subscribe(self, topic: str) -> None:
        if not self._client:
            raise MQTTError("Client is not connected")

        self._subscriptions.add(topic)

        self._logger.debug("Subscribing to topic: %s", topic)

        await self._client.subscribe(topic)

    async def set_message_callback(self, callback: MessageCallback) -> None:
        self._message_callback = callback

    # -------------------------
    # Internal
    # -------------------------

    async def _listen(self) -> None:
        """
        Single long-running task that routes all incoming messages.
        Triggers reconnect loop on unexpected disconnect.
        """
        assert self._client is not None

        try:
            async for msg in self._client.messages:
                topic = str(msg.topic)
                payload = msg.payload.decode()

                self._logger.debug("Received message on %s: %s", topic, payload)

                if self._message_callback:
                    try:
                        assert self._client is not None
                        await self._message_callback(topic, payload)
                    except Exception as e:
                        self._logger.error("Error in message callback for %s: %s", topic, e)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self._logger.warning("Listener dropped with error: %s", e)

            if self._shutdown:
                return

            if not self._config.reconnect:
                return

            if self._reconnect_task is None or self._reconnect_task.done():
                task = asyncio.create_task(self._reconnect_loop())
                task.add_done_callback(self._clear_reconnect_task)
                self._reconnect_task = task

    async def _reconnect_loop(self) -> None:
        """
        Async reconnect with exponential backoff.
        """
        async with self._reconnect_lock:
            delay = self._config.reconnect_delay_min

            while not self._shutdown:
                self._logger.info("Reconnecting in %.1fs...", delay)

                await asyncio.sleep(delay)

                try:
                    await self._start_connection()

                    # Re-subscribe to all known topics
                    for topic in self._subscriptions:
                        assert self._client is not None
                        await self._client.subscribe(topic)

                        self._logger.debug("Re-subscribed to topic: %s", topic)

                    self._logger.info("Reconnected successfully")
                    self._reconnect_task = None
                    return
                except asyncio.CancelledError:
                    self._logger.debug("Reconnect task cancelled")
                    raise
                except Exception as e:
                    self._logger.warning("Reconnect attempt failed: %s", e)
                    delay = min(delay * 2, self._config.reconnect_delay_max)

    def _ensure_reconnect_task(self) -> None:
        if self._reconnect_task is None or self._reconnect_task.done():
            self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    def _clear_reconnect_task(self, task: asyncio.Task) -> None:
        if self._reconnect_task is task:
            self._reconnect_task = None
