"""Configuration management system.

Layered, typed, event-aware configuration. Application code accesses
configuration exclusively through the ConfigurationProvider obtained from
a ConfigManager. YAML sources must never contain secrets; secrets are
supplied via environment variables.
"""

from lexmind.config.config_exceptions import (
    ConfigError,
    ConfigLoadError,
    ConfigValidationError,
    DeprecatedConfigKeyError,
    MissingConfigError,
    SecretInConfigError,
    UnknownConfigKeyError,
)
from lexmind.config.config_manager import ConfigManager
from lexmind.config.config_provider import ConfigurationProvider
from lexmind.config.config_schema import LexMindConfig
from lexmind.config.config_types import (
    Environment,
    LogLevel,
    SourceType,
)
from lexmind.config.environment import detect_environment, is_production

__all__ = [
    "ConfigError",
    "ConfigLoadError",
    "ConfigManager",
    "ConfigValidationError",
    "ConfigurationProvider",
    "DeprecatedConfigKeyError",
    "Environment",
    "LexMindConfig",
    "LogLevel",
    "MissingConfigError",
    "SecretInConfigError",
    "SourceType",
    "UnknownConfigKeyError",
    "detect_environment",
    "is_production",
]
