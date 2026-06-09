"""
Topic Manager

Responsible for building all MQTT topics for Home Assistant.

This module is fully independent of the MQTT transport layer.

Used by:
- sdk/core/entity_manager.py
"""

from ..config.device_fields import ALLOWED_FIELDS_PER_DOMAIN
from ..config.domains import HADomain
from ..exceptions import BuilderError


def _validate_domain(domain: HADomain) -> None:
    if not isinstance(domain, HADomain):
        raise BuilderError("Invalid domain")


def _validate_unique_id(unique_id: str) -> None:
    if not unique_id or not isinstance(unique_id, str):
        raise BuilderError("unique_id must be a non-empty string")


def _validate_prefix(prefix: str) -> None:
    if prefix == None:
        return
    if not isinstance(prefix, str):
        raise BuilderError("prefix must be a string")

# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def build_discovery_topic(domain: HADomain, unique_id: str, prefix: str) -> str:
    """
    Build Home Assistant discovery topic.

    Used by:
    - EntityManager.register()
    """

    _validate_domain(domain)
    _validate_unique_id(unique_id)
    _validate_prefix(prefix)

    # Fall back on default prefix if empty string or None
    if prefix == "" or prefix == None:
        prefix = "homeassistant"

    return f"{prefix}/{domain.value}/{unique_id}/config"


def build_state_topic(domain: HADomain, unique_id: str, prefix: str) -> str:
    """
    Build state topic.

    Used by:
    - EntityManager.update_state()
    """

    _validate_domain(domain)
    _validate_unique_id(unique_id)
    _validate_prefix(prefix)

    # Fall back on default prefix if empty string or None
    if prefix == "" or prefix == None:
        prefix = "homeassistant"

    schema = ALLOWED_FIELDS_PER_DOMAIN.get(domain)

    if not schema:
        raise BuilderError(f"No field definition found for domain {domain}")

    required = schema["required"]
    optional = schema["optional"]

    if "state_topic" not in required and "state_topic" not in optional:
        return ""

    return f"{prefix}/{domain.value}/{unique_id}/state"


def build_command_topic(
    domain: HADomain,
    unique_id: str,
    prefix: str,
) -> str:
    """
    Build command topic.

    Used by:
    - EntityManager.register()
    """

    _validate_domain(domain)
    _validate_unique_id(unique_id)

    schema = ALLOWED_FIELDS_PER_DOMAIN.get(domain)

    if not schema:
        raise BuilderError(f"No field definition found for domain {domain}")

    required = schema["required"]
    optional = schema["optional"]

    if "command_topic" not in required and "command_topic" not in optional:
        return ""

    return f"{prefix}/{domain.value}/{unique_id}/set"


def build_availability_topic(
    domain: HADomain,
    unique_id: str,
    prefix: str,
):
    _validate_domain(domain)
    _validate_unique_id(unique_id)

    schema = ALLOWED_FIELDS_PER_DOMAIN.get(domain)

    if not schema:
        raise BuilderError(f"No field definition found for domain {domain}")

    required = schema["required"]
    optional = schema["optional"]

    if "availability_topic" not in required and "availability_topic" not in optional:
        return ""

    return f"{prefix}/{domain.value}/{unique_id}/availability"
