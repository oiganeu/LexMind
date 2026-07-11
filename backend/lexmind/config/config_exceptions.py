"""Configuration exceptions."""

from lexmind.exceptions import LexMindError


class ConfigError(LexMindError):
    """Base class for configuration errors."""


class ConfigLoadError(ConfigError):
    """Raised when a configuration source cannot be loaded."""


class ConfigValidationError(ConfigError):
    """Raised when configuration fails validation."""


class MissingConfigError(ConfigError):
    """Raised when a required configuration value is missing."""


class UnknownConfigKeyError(ConfigError):
    """Raised when an unrecognized configuration key is present."""


class DeprecatedConfigKeyError(ConfigError):
    """Raised when a deprecated configuration key is present."""


class SecretInConfigError(ConfigError):
    """Raised when a secret is found in a non-secret configuration source."""
