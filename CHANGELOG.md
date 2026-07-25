# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

--

## [0.8.3] - 2026-07-25
- `payload_validators` - Changed the name validation as such that it also allows a name with None

--

## [0.8.2] - 2026-07-24
-   HA's shared MQTT entity config field controlling whether the
    entity's own name is combined with its device's name in the UI.
    Needed because light.py now sets name=None + has_entity_name=True
    for the single/primary entity of a device, to avoid HA 2023.8+'s
    "device name shown twice" bug (e.g. "Woonkamerverlichting
    Woonkamerverlichting") for an entity whose own name would
    otherwise equal its device's name.
- `device_fields` - Added "has_entity_name" in common_fields
- `test_device_fields` - Added a test for testing "has_entity_name"

--

## [0.8.1] - 2026-07-22
- The name within an entity needed a change. It can also be None, which was
  not implemented. 
- `entity` - Made a change to the variable name within the init block from
   type str towards str | None
- `entity`-  Made a change in the function _validate_basic on the check of
   name.

--

## [0.8.0] - 2026-07-12

### Fixed
- `discovery_payload` - Home Assistant's MQTT discovery schema expects
  device.identifiers as a plain string of list of strings and not a list of
  2-elements. Added a function which takes care of this (flattening).
- `test_discovery_payload` - Added tests which covers the additional added
  function.

---

## [0.7.0] - 2026-07-07

### Fixed
- `device_fields`- The light schema only reconized HA's old, deprecated
  per-feature-topic light schema (brightness_command_topic, color_temp_command_topic,
  ha_command_topic, etc - one dedicated topic pair per capability). Modern HA
  MQTT light schema (supported_color_modes, min_mireds, max_mireds, plus schema: "json"
  for RGB lights) - introduced in HA 20221.x - replaces that old approach. Except that
  replacement isn´t correct, because HA supports both the old and new light schemas.
  The change here is the add (not replace) of the new modern light schema.

### Changed
- `test_device_fields` - Needed changes to be able to test as well the new modern
  light schema.

### Added
- `test_entity`- Adding tests for the new modern light schema. 

---

## [0.6.0] - 2026-07-3

### Changed
- `async_sdk` - Added a forgotten wrapper for update_availability
- `test_async_sdk` - Added additional tests related to the changes in async_sdk
- `sdk` - Added a forgotten wrapper for update_availability
- `test_sdk` - Added additional tests realted to the changes in sdk

---

## [0.5.0] - 2026-07-02

### Changed
- `topic_manager` - some functions returned "" instead of None
- `discovery_payload` - can now handles with receive of a return None from topic_manager
- `entity_factory` - can now handles with receive of a return None from topic_manager
- `test_async_entity_manager` - adjusted to also check on None value returns
- `test_topic_manager` - adjusted to also check on None value returns
- `test_entity_manager` - adjusted to also check on None value returns

---

## [0.4.0] - 2026-06-26

### Added
- Plugin system: `IntegrationPlugin` and `AsyncIntegrationPlugin` abstract base classes
- Plugin system: `PluginManager` and `AsyncPluginManager` for lifecycle management
- `AsyncHASDK` — async entry point mirroring `HASDK` for the async path
- `HASDK.use_plugin()` and `HASDK.run()` — plugin lifecycle wiring for sync path
- `AsyncHASDK.use_plugin()` and `AsyncHASDK.run()` — plugin lifecycle wiring for async path
- `HASDK.shutdown()` and `AsyncHASDK.shutdown()` now call `stop_all()` on registered plugins
- `types.py` — shared `PublishPayload` and `StateValue` type aliases
- `py.typed` marker — package now fully typed and mypy-compatible (PEP 561)
- `PluginError` and `ConfigurationError` added to exception hierarchy
- `MQTTConnectionError` and `MQTTPublishError` added to exception hierarchy
- `BaseMQTTClient` and `BaseAsyncMQTTClient` now exported from `ha_mqtt_sdk.mqtt`
- `IntegrationPlugin` and `AsyncIntegrationPlugin` exported from top-level `ha_mqtt_sdk`
- `MQTTSettings`, `PublishPayload`, `StateValue` exported from top-level `ha_mqtt_sdk`
- All exceptions exported from top-level `ha_mqtt_sdk`
- `examples/plugin_usage/` — full sync plugin example with simulated hub
- `examples/async_plugin_usage/` — full async plugin example with WebSocket-style hub
- `examples/basic_usage/main.py` — updated to use `sdk.create_entity()` and `sdk.start()`
- 100% pytest coverage across all modules
- GitHub Actions workflows updated to `actions/checkout@v7` and `actions/setup-python@v6`
- CI matrix now tests Python 3.12, 3.13, and 3.14
- Mosquitto health check added to CI and `docker-compose.yml`
- `.pre-commit-config.yaml` — added `pre-commit-hooks` for file hygiene and debug statement detection
- Production `mosquitto.conf.example` added

### Changed
- `EntityManager` and `AsyncEntityManager` now accept `BaseMQTTClient` / `BaseAsyncMQTTClient`
  instead of concrete `PahoMQTTClient` / `AsyncMQTTClient` — enables custom transport injection
- `publish()` payload type widened from `str` to `PublishPayload` across all clients and base classes
- `update_state()` state type changed from `Any` to `StateValue` across sync and async managers
- `HASDK.shutdown()` changed from missing to implemented — calls plugin `stop_all()` then disconnects
- `AsyncHASDK.shutdown()` now calls plugin `stop_all()` before disconnecting MQTT
- `pyproject.toml` — development classifier updated from Alpha to Beta
- `pyproject.toml` — dev dependencies now have minimum version pins
- `pyproject.toml` — `[tool.mypy]` strengthened with `strict = true`
- `docker-compose.yml` — migrated to Compose V2 (removed `version` field)
- `docker-compose.yml` — test runner changed from `unittest` to `pytest` with coverage enforcement
- `Dockerfile` — updated to `python:3.14-slim`, installs from `pyproject.toml`
- `Makefile` — added `.PHONY`, `clean`, `format-check`, and `ci` targets
- `README.md` — fully rewritten to document sync/async paths and plugin system
- `CHANGELOG.md` — reformatted to follow Keep a Changelog specification

### Fixed
- `debug-statements` pre-commit hook catches leftover `print()` calls before commit
- `isinstance` checks in managers now use base classes instead of concrete implementations
- Version mismatch between `pyproject.toml` and `__init__.py` resolved via `importlib.metadata`
- `__init__.py` `LOGGER` global and `get_logger` import removed (unnecessary at package level)
- Typo in `[tool.coverage.report]` omit path (`pligin_interface` → removed entirely)
- `.pre-commit-config.yaml` renamed from `.yml` to `.yaml` (required by pre-commit)
- `docker-compose.yml` health check changed from `$SYS/#` to `nc -z localhost 1883`

### Removed
- `get_logger` removed from top-level `__init__.py` exports (internal utility)
- `EntityManager` and `AsyncEntityManager` removed from top-level `__all__` (internal)
- Dead exceptions removed: `DeviceError`, `CoreError`, `BuilderError` (never raised)
  — `BuilderError` retained as it is used in `builders/topic_manager.py`
- `pydantic` removed from `requirements.txt` (was listed but never used)
- `requirements.txt` replaced with `pip install -e ".[dev]"` pattern

---

## [0.3.0] - 2026-06-13

### Added
- Additional test functions for improved coverage

---

## [0.2.0] - 2026-06-01

### Added
- Ruff linting integration
- Code cleaned based on Ruff warnings

---

## [0.1.0] - 2026-05-01

### Added
- Initial release of HA-MQTT-SDK
- Basic publish/subscribe support
