import pytest

from ha_mqtt_sdk.config.mqtt import MQTTSettings
from ha_mqtt_sdk.exceptions import ConfigurationError


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {"host": ""},
            "MQTT host must not be empty",
        ),
        (
            {"port": 0},
            "MQTT port must be a positive integer",
        ),
        (
            {"keepalive": 0},
            "Keepalive must be > 0",
        ),
        (
            {"discovery_prefix": ""},
            "discovery_prefix must be a non-empty string",
        ),
        (
            {"discovery_prefix": "   "},
            "discovery_prefix must be a non-empty string",
        ),
        (
            {"reconnect_delay_min": 0},
            "Reconnect delay min must be > 0",
        ),
        (
            {
                "reconnect_delay_min": 10,
                "reconnect_delay_max": 5,
            },
            "Reconnect delay max must be >= reconnect delay min",
        ),
    ],
)
def test_mqtt_settings_validation_errors(kwargs, message):
    with pytest.raises(ConfigurationError, match=message):
        MQTTSettings(**kwargs)
