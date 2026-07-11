"""Plugin framework exceptions."""

from lexmind.exceptions import LexMindError


class PluginError(LexMindError):
    """Base class for plugin errors."""


class DuplicatePluginError(PluginError):
    """Raised when registering a plugin with a duplicate id."""


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""


class DependencyError(PluginError):
    """Base class for dependency resolution errors."""


class MissingDependencyError(DependencyError):
    """Raised when a declared dependency is not available."""


class CircularDependencyError(DependencyError):
    """Raised when the plugin dependency graph contains a cycle."""


class IncompatibleKernelError(PluginError):
    """Raised when a plugin requires an incompatible kernel version."""


class PluginDisabledError(PluginError):
    """Raised when an operation targets a disabled plugin."""
