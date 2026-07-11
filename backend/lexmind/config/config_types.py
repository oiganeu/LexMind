"""Configuration type definitions and enumerations."""

from enum import StrEnum


class Environment(StrEnum):
    """Deployment environment."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Logging verbosity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SourceType(StrEnum):
    """Configuration source categories, ordered by precedence."""

    DEFAULT = "default"
    ENVIRONMENT = "environment"
    PLUGIN = "plugin"
    WORKSPACE = "workspace"
    RUNTIME = "runtime"


# Precedence weight: higher overrides lower.
SOURCE_PRIORITY: dict[SourceType, int] = {
    SourceType.DEFAULT: 0,
    SourceType.ENVIRONMENT: 1,
    SourceType.PLUGIN: 2,
    SourceType.WORKSPACE: 3,
    SourceType.RUNTIME: 4,
}
