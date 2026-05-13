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

class EntityError(SDKError):
	"""Raised for entity-related issues."""
	pass

class DeviceError(SDKError):
	"""Raised for device_info-related issues."""
	pass

class MQTTError(SDKError):
	"""Raised when MQTT-related issues occur."""
	pass

class CoreError(SDKError):
	"""Raised when Core-related issues occur."""
	pass

class ConfigurationError(SDKError):
        """Raised for Config-related issues occur."""
        pass

class BuilderError(SDKError):
	"""Raised for Builders-related issues occur."""
	pass

