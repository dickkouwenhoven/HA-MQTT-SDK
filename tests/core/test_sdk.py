import pytest

from ha_mqtt_sdk.core.sdk import HASDK
from ha_mqtt_sdk.exceptions import SDKError

# -------------------------
# Init tests
# -------------------------


def test_init_requires_either_settings_or_client():
    with pytest.raises(SDKError):
        HASDK(mqtt_client=None, mqtt_settings=None)


def test_register_with_invalid_entity():
    with pytest.raises(SDKError):
        HASDK.register("Invalid Entity", "command_callback")


def test_update_state_with_invalid_entity():
    with pytest.raises(SDKError):
        HASDK.update_state("Invalid Entity", "ON")
