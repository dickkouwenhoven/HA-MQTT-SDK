"""
Tests for core/async_plugin_interface.py

Verifies that AsyncIntegrationPlugin:
- Cannot be instantiated directly (ABC)
- Requires all four abstract methods to be implemented
- Accepts a valid concrete async subclass
"""

import pytest

from ha_mqtt_sdk.core.async_plugin_interface import AsyncIntegrationPlugin


# ── helpers ───────────────────────────────────────────────────────────────────


class FullAsyncPlugin(AsyncIntegrationPlugin):
    """Concrete async implementation with all methods."""

    async def setup(self, sdk) -> None:
        pass

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def handle_command(self, topic: str, payload: str) -> None:
        pass


class MissingSetup(AsyncIntegrationPlugin):
    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def handle_command(self, topic: str, payload: str) -> None:
        pass


class MissingStart(AsyncIntegrationPlugin):
    async def setup(self, sdk) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def handle_command(self, topic: str, payload: str) -> None:
        pass


class MissingStop(AsyncIntegrationPlugin):
    async def setup(self, sdk) -> None:
        pass

    async def start(self) -> None:
        pass

    async def handle_command(self, topic: str, payload: str) -> None:
        pass


class MissingHandleCommand(AsyncIntegrationPlugin):
    async def setup(self, sdk) -> None:
        pass

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass


# ── abstract base class enforcement ──────────────────────────────────────────


def test_cannot_instantiate_directly():
    """AsyncIntegrationPlugin is abstract and must not be instantiated."""
    with pytest.raises(TypeError):
        AsyncIntegrationPlugin()  # type: ignore[abstract]


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
    """A complete async implementation must instantiate without error."""
    plugin = FullAsyncPlugin()

    assert isinstance(plugin, AsyncIntegrationPlugin)


@pytest.mark.asyncio
async def test_setup_is_awaitable():
    plugin = FullAsyncPlugin()
    await plugin.setup(sdk=None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_start_is_awaitable():
    plugin = FullAsyncPlugin()
    await plugin.start()


@pytest.mark.asyncio
async def test_stop_is_awaitable():
    plugin = FullAsyncPlugin()
    await plugin.stop()


@pytest.mark.asyncio
async def test_handle_command_is_awaitable():
    plugin = FullAsyncPlugin()
    await plugin.handle_command("home/switch/set", "ON")
