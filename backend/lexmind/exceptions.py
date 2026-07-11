"""Global exception hierarchy."""

from lexmind.__about__ import __version__


class LexMindError(Exception):
    """Base class for LexMind errors."""


class ConfigurationError(LexMindError):
    """Raised when configuration is invalid."""


class ValidationError(LexMindError):
    """Raised when input validation fails."""


class PluginError(LexMindError):
    """Raised when a plugin fails to load or execute."""


class InfrastructureError(LexMindError):
    """Raised when an external system interaction fails."""


class NotImplementedYetError(LexMindError):
    """Raised for features not yet implemented."""

    def __init__(self, feature: str = "This feature") -> None:
        super().__init__(f"{feature} is not implemented yet (LexMind {__version__}).")
