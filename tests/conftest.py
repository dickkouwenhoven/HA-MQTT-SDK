from collections.abc import Awaitable, Callable
from typing import Any

import pytest

from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.mqtt.async_client import AsyncMQTTClient
from ha_mqtt_sdk.mqtt.paho_client import PahoMQTTClient


class MockMQTTClient(PahoMQTTClient):
    def __init__(self):
        self.published: list[tuple[str, Any, bool]] = []
        self.subscribed: list[str] = []
        self.callback: Callable[[str, str], None] | None = None
        self.last_will = None

    def publish(
        self,
        topic,
        payload,
        retain=False,
    ):
        self.published.append((topic, payload, retain))

    def subscribe(
        self,
        topic,
    ):
        self.subscribed.append(topic)

    def set_message_callback(
        self,
        callback,
    ):
        self.callback = callback

    def set_last_will(
        self,
        topic,
        payload="offline",
    ):
        self.last_will = (topic, payload)

    def simulate_message(self, topic, payload):
        if self.callback:
            self.callback(topic, payload)    

    def connect(self):
        pass

    def disconnect(self):
        pass

class AsyncMockMQTTClient(AsyncMQTTClient):
    def __init__(self):
        self.published: list[tuple[str, Any, bool]] = []
        self.subscribed: list[str]  = []
        self.callback: Callable[[str, str], Awaitable[None]] | None = None
        self.last_will = None

    async def publish(
        self,
        topic,
        payload,
        retain=False,
    ):
        self.published.append((topic, payload, retain))

    async def subscribe(
        self,
        topic,
    ):
        self.subscribed.append(topic)

    def set_message_callback(
        self,
        callback,
    ):
        self.callback = callback

    def set_last_will(
        self,
        topic,
        payload="offline",
    ):
        self.last_will = (topic, payload)

    async def simulate_message(self, topic, payload):
        if self.callback:
            await self.callback(topic, payload)

    async def connect(self):
        pass

    async def disconnect(self):
        pass

@pytest.fixture
def mqtt_client_sync():
    return MockMQTTClient()


@pytest.fixture
def mqtt_client_async():
    return AsyncMockMQTTClient()


@pytest.fixture
def mqtt_settings():
    return MQTTSettings(discovery_prefix="homeassistant")
