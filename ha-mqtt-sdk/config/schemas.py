"""
schemas.py

Comprehensive Home Assistant MQTT component schemas.

This module defines:
- All supported Home Assistant MQTT domains
- Required fields per domain
- Common optional fields

Design principles:
- Strict validation on required fields
- Flexible optional fields (HA evolves frequently)
- Maintainability over hardcoding every HA attribute

Used by:
- sdk/builders/discovery_payload.py
"""

from dataclasses import dataclass
from typing import Set, Dict

from .domains import HADomain


# ---------------------------------------------------------------------------
# Schema model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ComponentSchema:
	domain: HADomain
	required_fields: Set[str]
	optional_fields: Set[str]


# ---------------------------------------------------------------------------
# Common fields (shared across most components)
# ---------------------------------------------------------------------------

COMMON_REQUIRED = {
	"name",
	"unique_id"
}

COMMON_OPTIONAL = {
	"state_topic",
	"command_topic",
	"availability_topic",
	"payload_available",
	"payload_not_available",
	"device",
	"icon",
	"unit_of_measurement",
	"value_template",
	"json_attributes_topic",
	"json_attributes_template",
	"expire_after",
	"enabled_by_default",
	"entity_category",
	"qos",
	"retain",
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _schema(
	domain: HADomain,
	required: Set[str],
) -> ComponentSchema:
	return ComponentSchema(
		domain=domain,
		required_fields=required,
		optional_fields=COMMON_OPTIONAL,
	)


# ---------------------------------------------------------------------------
# Full domain coverage
# ---------------------------------------------------------------------------

SCHEMAS: Dict[HADomain, ComponentSchema] = {

	# ---------------------------
	# Sensors
	# ---------------------------
	HADomain.SENSOR: _schema(
		HADomain.SENSOR,
		COMMON_REQUIRED | {"state_topic"},
	),

	HADomain.BINARY_SENSOR: _schema(
		HADomain.BINARY_SENSOR,
		COMMON_REQUIRED | {"state_topic"},
	),

	HADomain.NUMBER: _schema(
		HADomain.NUMBER,
		COMMON_REQUIRED | {"state_topic", "command_topic"},
	),

	HADomain.TEXT: _schema(
		HADomain.TEXT,
		COMMON_REQUIRED | {"state_topic", "command_topic"},
	),

	HADomain.SELECT: _schema(
		HADomain.SELECT,
		COMMON_REQUIRED | {"state_topic", "command_topic"},
	),

	# ---------------------------
	# Actuators
	# ---------------------------
	HADomain.SWITCH: _schema(
		HADomain.SWITCH,
		COMMON_REQUIRED | {"state_topic", "command_topic"},
	),

	HADomain.LIGHT: _schema(
		HADomain.LIGHT,
		COMMON_REQUIRED | {"command_topic"},
	),

	HADomain.FAN: _schema(
		HADomain.FAN,
		COMMON_REQUIRED | {"command_topic"},
	),

	HADomain.COVER: _schema(
		HADomain.COVER,
		COMMON_REQUIRED | {"command_topic"},
	),

	HADomain.LOCK: _schema(
		HADomain.LOCK,
		COMMON_REQUIRED | {"command_topic"},
	),

	HADomain.VALVE: _schema(
		HADomain.VALVE,
		COMMON_REQUIRED | {"command_topic"},
	),

	HADomain.WATER_HEATER: _schema(
		HADomain.WATER_HEATER,
		COMMON_REQUIRED | {"command_topic"},
	),

	HADomain.CLIMATE: _schema(
		HADomain.CLIMATE,
		COMMON_REQUIRED | {"command_topic"},
	),

	HADomain.HUMIDIFIER: _schema(
		HADomain.HUMIDIFIER,
		COMMON_REQUIRED | {"command_topic"},
	),

	HADomain.VACUUM: _schema(
		HADomain.VACUUM,
		COMMON_REQUIRED | {"command_topic"},
	),

	HADomain.LAWN_MOWER: _schema(
		HADomain.LAWN_MOWER,
		COMMON_REQUIRED | {"command_topic"},
	),

	# ---------------------------
	# Stateless / triggers
	# ---------------------------
	HADomain.BUTTON: _schema(
		HADomain.BUTTON,
		COMMON_REQUIRED | {"command_topic"},
	),

	HADomain.EVENT: _schema(
		HADomain.EVENT,
		COMMON_REQUIRED | {"state_topic"},
	),

	HADomain.DEVICE_TRIGGER: _schema(
		HADomain.DEVICE_TRIGGER,
		{"automation_type", "topic", "type"},
	),

	# ---------------------------
	# Other
	# ---------------------------
	HADomain.ALARM_CONTROL_PANEL: _schema(
		HADomain.ALARM_CONTROL_PANEL,
		COMMON_REQUIRED | {"command_topic"},
	),

	HADomain.SIREN: _schema(
		HADomain.SIREN,
		COMMON_REQUIRED | {"command_topic"},
	),

	HADomain.UPDATE: _schema(
		HADomain.UPDATE,
		COMMON_REQUIRED | {"state_topic"},
	),

	HADomain.SCENE: _schema(
		HADomain.SCENE,
		COMMON_REQUIRED | {"command_topic"},
	),

	HADomain.DEVICE_TRACKER: _schema(
		HADomain.DEVICE_TRACKER,
		COMMON_REQUIRED | {"state_topic"},
	),
}
