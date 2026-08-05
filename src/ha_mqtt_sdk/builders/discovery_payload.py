"""
Discovery Payload Builder

Responsible for building Home Assistant MQTT discovery payloads.

This module:
- Translates Entity → HA payload

Used by:
- sdk/core/entity_manager.py
"""

from typing import Any

from ..exceptions import EntityError
from ..models.device_info import DeviceInfo
from ..models.entity import Entity
from ..utils.logger import get_logger
from ..validators.payload_validator import validate_discovery_payload
from .topic_manager import (
    build_availability_topic,
    build_command_topic,
    build_state_topic,
)

_logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_entity(entity: Entity) -> None:
    if not isinstance(entity, Entity):
        raise EntityError("Invalid entity")


def _build_device_block(entity: Entity) -> DeviceInfo:
    """
    Build device block for HA.
    """

    _validate_entity(entity)
    entity.validate()

    return entity.device_info or {}


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------


def build_discovery_payload(
    entity: Entity,
    prefix: str,
) -> dict[str, Any]:
    """
    Build full Home Assistant MQTT discovery payload.

    Responsibilities:
    - Build HA-compatible discovery payload
    - Add optional device block
    - Merge extra attributes

    Used by:
    - EntityManager.register()
    """

    _validate_entity(entity)
    entity.validate()

    # ------------------------------------------------------
    # Base payload
    # ------------------------------------------------------

    payload: dict[str, Any] = {
        "name": entity.name,
        "unique_id": entity.unique_id,
    }

    state_topic = build_state_topic(
        entity.domain,
        entity.unique_id,
        prefix,
    )

    if state_topic:
        payload["state_topic"] = state_topic

    # ------------------------------------------------------
    # Optional command topic
    # ------------------------------------------------------

    command_topic = build_command_topic(
        entity.domain,
        entity.unique_id,
        prefix,
    )

    if command_topic:
        payload["command_topic"] = command_topic

    # ------------------------------------------------------
    # Optional availability topic
    # ------------------------------------------------------

    availability_topic = build_availability_topic(
        entity.domain,
        entity.unique_id,
        prefix,
    )

    if availability_topic:
        payload["availability_topic"] = availability_topic
        payload["payload_available"] = "online"
        payload["payload_not_available"] = "offline"
    
    # ------------------------------------------------------
    # Optional device block
    # ------------------------------------------------------

    device_block = _build_device_block(entity)

    if device_block:
        payload["device"] = _serialize_device_block(device_block)

    # ------------------------------------------------------
    # Extra user-defined attributes
    # ------------------------------------------------------

    if entity.extra:
        payload.update(entity.extra)

    # ------------------------------------------------------
    # Payload validation
    # ------------------------------------------------------
    validate_discovery_payload(
        payload=payload,
        domain=entity.domain,
    )

    # ------------------------------------------------------
    # Logging
    # ------------------------------------------------------

    _logger.debug(
        "Discovery payload built for %s: %s",
        entity.name,
        entity.unique_id,
    )

    return payload


def _serialize_device_block(device_info: DeviceInfo) -> dict[str, Any]:
    """
    Convert SDK DeviceInfo representation into HA MQTT discovery format.

    HA's MQTT discovery schema requires device.identifiers to be a list
    of plain strings (or a single string) — not the SDK's internal
    list[tuple[str, str]] representation. Sending the tuple form as-is
    causes HA to reject the entire discovery payload with
    "value should be a string @ data['device']['identifiers'][0]".
    Same reasoning applies to via_device. connections keeps its
    [[type, value], ...] shape, since that IS the shape HA expects.

    Note: the three special fields are read from device_info (the
    original TypedDict) rather than from the `dict(device_info)` copy
    below. dict(TypedDict_instance) erases the precise per-key typing
    (mypy can only see it as dict[str, object], since a TypedDict's
    values aren't guaranteed homogeneous), which is what caused the
    "object has no attribute '__iter__'" / "not indexable" mypy
    errors. Reading from device_info.get(...) preserves DeviceInfo's
    real per-field types (list[tuple[str, str]], tuple[str, str]).
    """

    device: dict[str, Any] = dict(device_info)

    identifiers = device_info.get("identifiers")
    if identifiers is not None:
        device["identifiers"] = [f"{domain}_{identifier}" for domain, identifier in identifiers]

    connections = device_info.get("connections")
    if connections:
        device["connections"] = [
            [connection_type, connection_value] for connection_type, connection_value in connections
        ]

    via_device = device_info.get("via_device")
    if via_device:
        device["via_device"] = f"{via_device[0]}_{via_device[1]}"

    return device
