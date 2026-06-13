# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog:
https://keepachangelog.com/en/1.1.0/

## [0.4.0]

### Added
- Improved Async MQTT client using aiomqtt
- Improved Sync MQTT client using paho-mqtt
- Automatic reconnect with exponential backoff
- Subscription tracking with auto re-subscribe
- Last Will and Testament (LWT) support

### Fixed
- Improved reconnect stability in edge cases
- Fixed callback exception handling in message routing

### Changed
- Refactored reconnect logic for sync/async parity
- Improved logging consistency

---

## [0.3.0] - 2026-06-13

### Added
- Adding of additional test functions

---

## [0.2.0] - 2026-06-01

### Added
- Add Ruff testing
- Cleaned files based upon ruff warnings

---

## [0.1.0] - 2026-05-01
- Initial release of HA MQTT SDK
- Basic publish/subscribe support
