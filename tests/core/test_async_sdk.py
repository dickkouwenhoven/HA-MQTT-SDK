import pytest

from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.core.async_sdk import AsyncHASDK
from ha_mqtt_sdk.exceptions import SDKError
from ha_mqtt_sdk.mqtt.async_client import AsyncMQTTClient

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
