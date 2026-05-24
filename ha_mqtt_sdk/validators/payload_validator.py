"""
Payload validation utilities.
"""

from __future__ import annotations

import json

from typing import Any
from collections.abc import Mapping

from ..config.domains import HADomain
from ..exceptions import ValidationError


def validate_json_serializable(
    payload: Any,
) -> None:
    """
    Ensure payload is JSON serializable.
    """

    try:
        json.dumps(payload)

    except (
        TypeError,
        ValueError,
    ) as err:
        raise ValidationError(
            f"Payload is not JSON serializable: {err}"
        ) from err


def validate_discovery_payload(
    payload: Mapping[str, Any],
    domain: HADomain,
) -> None:
    """
    Validate Home Assistant discovery payload.
    """

    if not isinstance(payload, Mapping):
        raise ValidationError(
            "Discovery payload must be a mapping"
        )

    if not payload:
        raise ValidationError(
            "Discovery payload cannot be empty"
        )

    validate_json_serializable(payload)

    unique_id = payload.get("unique_id")

    if not unique_id:
        raise ValidationError(
            "Discovery payload requires unique_id"
        )

    name = payload.get("name")

    if not name:
        raise ValidationError(
            "Discovery payload requires name"
        )

    state_topic = payload.get("state_topic")

    if not state_topic:
        raise ValidationError(
            "Discovery payload requires state_topic"
        )

    if not isinstance(state_topic, str):
        raise ValidationError(
            "state_topic must be a string"
        )
