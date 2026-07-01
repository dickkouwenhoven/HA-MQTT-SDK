"""
Payload validation utilities.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from ..config.domains import HADomain
from ..exceptions import ValidationError


def validate_json_serializable(
    payload: Any,
) -> None:
    """
    Ensure payload is JSON serializable.
    """
    _validate_json_value(
        value=payload,
        path="payload",
    )


def _validate_json_value(
    value: Any,
    path: str,
) -> None:
    """
    Recursively validate JSON serializability
    and provide precise error locations.
    """
    if value is None:
        return

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return

    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(
                item,
                f"{path}[{index}]",
            )
        return

    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _validate_json_value(
                item,
                f"{path}[{index}]",
            )

    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValidationError(f"{path}: JSON object keys must be strings")

            _validate_json_value(
                item,
                f"{path}.{key}",
            )
        return

    try:
        json.dumps(value)

    except (
        TypeError,
        ValueError,
    ) as err:
        raise ValidationError(
            f"{path}: value of type {type(value).__name__} is not JSON serializable"
        ) from err


def validate_discovery_payload(
    payload: Mapping[str, Any],
    domain: HADomain,
) -> None:
    """
    Validate Home Assistant discovery payload.
    """

    if not isinstance(payload, Mapping):
        raise ValidationError("Discovery payload must be a mapping")

    if not payload:
        raise ValidationError("Discovery payload cannot be empty")

    validate_json_serializable(payload)

    unique_id = payload.get("unique_id")

    if not unique_id:
        raise ValidationError("Discovery payload requires unique_id")

    name = payload.get("name")

    if not name:
        raise ValidationError("Discovery payload requires name")

    # Only validate state_topic if this domain supports it.
    # Command-only domains (e.g. BUTTON, SCENE) have no state_topic - that is valid.
    # Import here to avoid circular import
    from ..config.device_fields import ALLOWED_FIELDS_PER_DOMAIN

    schema = ALLOWED_FIELDS_PER_DOMAIN.get(domain)
    if schema:
        domain_supports_state = (
            "state_topic" in schema["required"] or "state_topic" in schema["optional"]
        )
        if domain_supports_state:
            state_topic = payload.get("state_topic")
            if not state_topic:
                raise ValidationError(
                    f"Discovery payload for domain '{domain.value}' requires state_topic"
                )
            if not isinstance(state_topic, str):
                raise ValidationError("state_topic must be as string")
