"""
HASDK - High-level orchestration entrypoint.

This is the main interface for users of the SDK.

Responsibilities:
- Initialize MQTT client (or accept injected client)
- Manage entity lifecycle via EntityManager
- Provide simple API for:
    - register
    - state updates
    - command handling

Used by:
- End users of the SDK
"""

from collections.abc import Callable

from ..mqtt import (
	BaseMQTTClient,
	PahoMQTTClient,
)
from ..models.entity import Entity
from ..utils.logger import get_logger
from .entity_manager import EntityManager
from ..config.mqtt import MQTTSettings
from ..exceptions import SDKError

class HASDK:
	def __init__(
		self,
		mqtt_config: MQTTSettings | None = None,
		mqtt_client: BaseMQTTClient | None = None,
		mqtt_settings: MQTTSettings | None = None,
	):
		"""
		Initialize SDK.

		Either mqtt_config OR mqtt_client must be provided.
		"""

		self._logger = get_logger(__name__)
		self._mqtt_settings = mqtt_settings or MQTTSettings()

		if not mqtt_client and not mqtt_config:
			raise SDKError("Provide either mqtt_config or mqtt_client")

		if mqtt_client and mqtt_config:
			self._logger.warning(
				"Both mqtt_client and mqtt_config provided. Using mqtt_client."
			)

		# Dependency injection (preferred)
		if mqtt_client:
			self._mqtt = mqtt_client
		else:
			self._mqtt = PahoMQTTClient(mqtt_config)

		self._entity_manager = EntityManager(self._mqtt, self._mqtt_settings)

	# -------------------------
	# Public API
	# -------------------------

	def start(self) -> None:
		"""
		Start MQTT connection.
		"""
		self._logger.info("Starting HASDK")
		self._mqtt.connect()

	def shutdown(self) -> None:
		"""
		Gracefully shutdown SDK.
		"""
		self._logger.info("Shutting down HASDK")
		self._mqtt.disconnect()

	def register(self, entity: Entity) -> None:
		"""
		Register entity in Home Assistant.

		Used by:
		- user code
		"""
		if not isinstance(entity, Entity):
			raise SDKError("Invalid entity")

		self._entity_manager.register(entity)

	def update_state(self, entity: Entity, payload: dict) -> None:
		"""
		Update entity state.

		Used by:
		- user code
		"""
		if not isinstance(entity, Entity):
			raise SDKError("Invalid entity")
		
		if not isinstance(payload, dict):
			raise SDKError("Payload must be dict")

		self._entity_manager.update_state(entity, payload)

	def on_command(self, entity: Entity, callback: Callable[[str, str], None]) -> None:
		"""
		Register global command handler.

		Used by:
		- user code (Dirigera integration)
		"""
		if not isinstance(entity, Entity):
			raise SDKError("Invalid entity")
		
		if not callable(callback):
			raise SDKError("Callback must be callable")

		self._entity_manager.set_command_callback(entity, callback)
