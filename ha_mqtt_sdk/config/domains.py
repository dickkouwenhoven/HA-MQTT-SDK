"""
Home Assistant Domains - Complete MQTT Coverage

Single source of truth for all supported HA domains.
"""

from enum import Enum


class HADomain(str, Enum):
	ALARM_CONTROL_PANEL = "alarm_control_panel"
	BINARY_SENSOR = "binary_sensor"
	BUTTON = "button"
	CAMERA = "camera"
	CLIMATE = "climate"
	COVER = "cover"
	DATE = "date"
	DATETIME = "datetime"
	DEVICE_TRACKER = "device_tracker"
	DEVICE_TRIGGER = "device_trigger"
	EVENT = "event"
	FAN = "fan"
	HUMIDIFIER = "humidifier"
	IMAGE = "image"
	LAWN_MOWER = "lawn_mower"
	LIGHT = "light"
	LOCK = "lock"
	NOTIFY = "notify"
	NUMBER = "number"
	SCENE = "scene"
	SELECT = "select"
	SENSOR = "sensor"
	SIREN = "siren"
	SWITCH = "switch"
	TAG = "tag"
	TEXT = "text"
	TIME = "time"
	UPDATE = "update"
	VACUUM = "vacuum"
	VALVE = "valve"
	WATER_HEATER = "water_heater"

	@classmethod
	def has_value(cls, value: str) -> bool:
		return value in cls._value2member_map_
