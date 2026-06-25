"""
exceptions.py

Custom exception hierarchy for HASDK.

Purpose:
- Provide consistent error handling
- Allow users to catch SDK-specific errors
"""


class SDKError(Exception):
    """Base exception for all SDK errors."""

    pass


class ValidationError(SDKError):
    """Raised when input validation fails."""

    pass


class EntityError(ValidationError):
    """Raised for entity-related issues."""

    pass


class SchemaError(ValidationError):
    """Raised for schema-related issues."""

    pass


class MQTTError(SDKError):
    """Raised when MQTT-related issues occur."""

    pass


class MQTTConnectionError(MQTTError):
    """Raised when MQTT-connection issues occur."""

    pass


class MQTTPublishError(MQTTError):
    """Raised when MQTT-publish issues occur."""

    pass


class ConfigurationError(SDKError):
    """Raised for Config-related issues occur."""

    pass


class BuilderError(SDKError):
    """Raised for Builders-related issues occur."""

    pass


class PluginError(SDKError):
    """Raised for plugin registration and lifecycle issues."""

    pass
