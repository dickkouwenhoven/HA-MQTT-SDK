"""
Device fields per Home Assistant domain

Contains the default set of fields for each device type.
Imports HADomain from domains.py for single source of truth.
"""

from .domains import HADomain


def _optional(*parts: set[str], required: set[str] | None = None) -> set[str]:
    result: set[str] = set()
    for part in parts:
        result |= part

    if required:
        result -= required

    return result


# ---------------------------------------------------------------------------
# Generic fields applied to most devices
# ---------------------------------------------------------------------------

COMMON_FIELDS: set[str] = {
    "availability",
    "availability_topic",
    "availability_mode",
    "availability_template",
    "device",
    "device_class",
    "enabled_by_default",
    "entity_category",
    "icon",
    "json_attributes_topic",
    "json_attributes_template",
    "object_id",
    "qos",
    "retain",
}

STATE_FIELDS: set[str] = {
    "state_topic",
    "value_template",
    "state_class",
    "expire_after",
    "force_update",
}

COMMAND_FIELDS: set[str] = {
    "command_topic",
    "payload_on",
    "payload_off",
    "state_value_template",
    "optimistic",
}

# ---------------------------------------------------------------------------
# All device type fields
# Each HADomain maps to a dict with required and optional fields
# ---------------------------------------------------------------------------

ALLOWED_FIELDS_PER_DOMAIN: dict[HADomain, dict[str, set[str]]] = {
    HADomain.ALARM_CONTROL_PANEL: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {
            "state_topic",
            "code",
            "code_arm_required",
            "payload_arm_home",
            "payload_arm_away",
            "payload_arm_night",
            "payload_arm_vacation",
            "payload_disarm",
        },
    },
    HADomain.BUTTON: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS | {"payload_press"},
    },
    HADomain.DEVICE_TRACKER: {
        "required": {"name", "state_topic", "unique_id"},
        "optional": COMMON_FIELDS | {"payload_home", "payload_not_home", "source_type"},
    },
    HADomain.DEVICE_TRIGGER: {
        "required": {"automation_type", "topic", "type", "subtype", "device"},
        "optional": {"payload", "value_template", "qos"},
    },
    HADomain.EVENT: {
        "required": {"name", "state_topic", "unique_id"},
        "optional": COMMON_FIELDS | {"event_types", "value_template"},
    },
    HADomain.HUMIDIFIER: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {
            "state_topic",
            "target_humidity_command_topic",
            "target_humidity_state_topic",
            "min_humidity",
            "max_humidity",
        },
    },
    HADomain.LAWN_MOWER: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {
            "state_topic",
            "payload_start",
            "payload_pause",
            "payload_stop",
            "payload_return_to_base",
        },
    },
    HADomain.SCENE: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS | {"payload_on"},
    },
    HADomain.SIREN: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {
            "state_topic",
            "available_tones",
            "tone_command_topic",
            "tone_state_topic",
            "duration_command_topic",
            "duration_state_topic",
        },
    },
    HADomain.UPDATE: {
        "required": {"name", "state_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {
            "command_topic",
            "payload_install",
            "latest_version_template",
            "installed_version_template",
        },
    },
    HADomain.VALVE: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {
            "state_topic",
            "position_command_topic",
            "position_state_topic",
            "set_position_template",
        },
    },
    HADomain.SENSOR: {
        "required": {"name", "state_topic", "unique_id"},
        "optional": _optional(
            COMMON_FIELDS,
            STATE_FIELDS,
            {"device_class", "unit_of_measurement", "state_class", "last_reset_value_template"},
            required={"name", "state_topic", "unique_id"},
        ),
    },
    HADomain.BINARY_SENSOR: {
        "required": {"name", "state_topic", "unique_id"},
        "optional": COMMON_FIELDS | STATE_FIELDS | {"device_class", "payload_on", "payload_off"},
    },
    HADomain.SWITCH: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS | COMMAND_FIELDS | {"state_topic"},
    },
    HADomain.LIGHT: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | COMMAND_FIELDS
        | {
            "state_topic",
            "brightness_command_topic",
            "brightness_state_topic",
            "brightness_scale",
            "color_temp_command_topic",
            "color_temp_state_topic",
            "effect_command_topic",
            "effect_state_topic",
            "hs_command_topic",
            "hs_state_topic",
            "rgb_command_topic",
            "rgb_state_topic",
            "xy_command_topic",
            "xy_state_topic",
        },
    },
    HADomain.COVER: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {
            "state_topic",
            "position_command_topic",
            "tilt_command_topic",
            "tilt_state_topic",
            "set_position_template",
            "set_tilt_template",
        },
    },
    HADomain.FAN: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {
            "state_topic",
            "percentage_command_topic",
            "percentage_state_topic",
            "preset_mode_command_topic",
            "preset_mode_state_topic",
            "oscillation_command_topic",
            "oscillation_state_topic",
        },
    },
    HADomain.LOCK: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS | {"state_topic", "payload_lock", "payload_unlock"},
    },
    HADomain.NUMBER: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS | {"state_topic", "min", "max", "step", "mode"},
    },
    HADomain.SELECT: {
        "required": {"name", "command_topic", "options", "unique_id"},
        "optional": COMMON_FIELDS | {"state_topic"},
    },
    HADomain.TEXT: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS | {"state_topic", "min", "max", "pattern"},
    },
    HADomain.VACUUM: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {"state_topic", "fan_speed_command_topic", "fan_speed_state_topic", "send_command_topic"},
    },
    HADomain.WATER_HEATER: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {"state_topic", "temperature_command_topic", "temperature_state_topic", "modes"},
    },
    HADomain.CLIMATE: {
        "required": {"name", "mode_command_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {
            "mode_state_topic",
            "temperature_command_topic",
            "temperature_state_topic",
            "current_temperature_topic",
            "temperature_unit",
            "modes",
            "fan_mode_command_topic",
            "fan_mode_state_topic",
            "swing_mode_command_topic",
            "swing_mode_state_topic",
            "preset_mode_command_topic",
            "preset_mode_state_topic",
            "action_topic",
            "power_command_topic",
            "power_state_topic",
        },
    },
    HADomain.CAMERA: {
        "required": {"name", "topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {
            "image_encoding",
            "content_type",
        },
    },
    HADomain.DATE: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {
            "state_topic",
        },
    },
    HADomain.DATETIME: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {
            "state_topic",
        },
    },
    HADomain.TIME: {
        "required": {"name", "command_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {
            "state_topic",
        },
    },
    HADomain.IMAGE: {
        "required": {"name", "image_topic", "unique_id"},
        "optional": COMMON_FIELDS
        | {
            "content_type",
        },
    },
    HADomain.NOTIFY: {
        "required": {"name", "command_topic"},
        "optional": COMMON_FIELDS
        | {
            "title",
            "icon",
        },
    },
    HADomain.TAG: {
        "required": {"topic"},
        "optional": {
            "value_template",
            "qos",
        },
    },
}
