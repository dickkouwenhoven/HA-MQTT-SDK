import pytest
import pytest_asyncio

from ha_mqtt_sdk.config.domains import HADomain
from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.core.async_sdk import AsyncHASDK
from ha_mqtt_sdk.core.entity_factory import create_entity
from ha_mqtt_sdk.exceptions import SDKError
from ha_mqtt_sdk.models.entity import Entity
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

    entity: Entity = create_entity(
        domain=HADomain.SWITCH,
        name="Relay",
        unique_id="relay_1",
    )

    entity.domain = "Invalid Domain"

    with pytest.raises(SDKError):
        sdk.on_command(entity, "command_callback")
