"""
Tests for core/plugin_interface.py

Verifies that IntegrationPlugin:
- Cannot be instantiated directly (ABC)
- Requires all four abstract methods to be implemented
- Accepts a valid concrete subclass
"""

import pytest

from ha_mqtt_sdk.core.plugin_interface import IntegrationPlugin

# ── helpers ───────────────────────────────────────────────────────────────────


class FullPlugin(IntegrationPlugin):
    """Concrete implementation with all methods."""

    def setup(self, sdk) -> None:
        pass

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def handle_command(self, topic: str, payload: str) -> None:
        pass


class MissingSetup(IntegrationPlugin):
    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def handle_command(self, topic: str, payload: str) -> None:
        pass


class MissingStart(IntegrationPlugin):
    def setup(self, sdk) -> None:
        pass

    def stop(self) -> None:
        pass

    def handle_command(self, topic: str, payload: str) -> None:
        pass


class MissingStop(IntegrationPlugin):
    def setup(self, sdk) -> None:
        pass

    def start(self) -> None:
        pass

    def handle_command(self, topic: str, payload: str) -> None:
        pass


class MissingHandleCommand(IntegrationPlugin):
    def setup(self, sdk) -> None:
        pass

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass


# ── abstract base class enforcement ──────────────────────────────────────────


def test_cannot_instantiate_directly():
    """IntegrationPlugin is abstract and must not be instantiated."""
    with pytest.raises(TypeError):
        IntegrationPlugin()  # type: ignore[abstract]


def test_missing_setup_raises():
    with pytest.raises(TypeError):
        MissingSetup()  # type: ignore[abstract]


def test_missing_start_raises():
    with pytest.raises(TypeError):
        MissingStart()  # type: ignore[abstract]


def test_missing_stop_raises():
    with pytest.raises(TypeError):
        MissingStop()  # type: ignore[abstract]


def test_missing_handle_command_raises():
    with pytest.raises(TypeError):
        MissingHandleCommand()  # type: ignore[abstract]


# ── valid concrete subclass ───────────────────────────────────────────────────


def test_full_implementation_instantiates():
    """A complete implementation must instantiate without error."""
    plugin = FullPlugin()

    assert isinstance(plugin, IntegrationPlugin)


def test_setup_is_callable():
    plugin = FullPlugin()
    plugin.setup(sdk=None)  # type: ignore[arg-type]


def test_start_is_callable():
    plugin = FullPlugin()
    plugin.start()


def test_stop_is_callable():
    plugin = FullPlugin()
    plugin.stop()


def test_handle_command_is_callable():
    plugin = FullPlugin()
    plugin.handle_command("home/switch/set", "ON")
