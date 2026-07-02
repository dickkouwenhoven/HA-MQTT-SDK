# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

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
