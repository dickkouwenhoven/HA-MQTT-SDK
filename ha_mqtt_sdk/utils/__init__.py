"""
Utility module for Home Assistant MQTT SDK.

This package contains shared utilities used across the SDK.

Exposed functionality:
- get_logger: Centralized logging utility (dual-mode)

Design principles:
- Only expose public utility functions
- Keep internal helpers private (prefixed with _)
- Maintain backward compatibility for SDK users
"""

from .logger import setup_logger, get_logger

__all__ = [
	"setup_logger",
	"get_logger",
]
