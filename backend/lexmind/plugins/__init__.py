"""Plugin framework for LexMind."""

from lexmind.plugins.discovery import Discovery, PluginCandidate
from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_context import PluginContext
from lexmind.plugins.plugin_exceptions import (
    CircularDependencyError,
    DependencyError,
    DuplicatePluginError,
    IncompatibleKernelError,
    MissingDependencyError,
    PluginDisabledError,
    PluginError,
    PluginLoadError,
)
from lexmind.plugins.plugin_loader import PluginLoader
from lexmind.plugins.plugin_manager import (
    PluginManager,
    parse_version,
    validate_dependencies,
    version_in_range,
)
from lexmind.plugins.plugin_manifest import PluginManifest
from lexmind.plugins.plugin_metadata import PluginMetadata
from lexmind.plugins.plugin_registry import PluginRegistry
from lexmind.plugins.plugin_state import PluginState

__all__ = [
    "BasePlugin",
    "CircularDependencyError",
    "DependencyError",
    "Discovery",
    "DuplicatePluginError",
    "IncompatibleKernelError",
    "MissingDependencyError",
    "parse_version",
    "PluginCandidate",
    "PluginCapability",
    "PluginContext",
    "PluginDisabledError",
    "PluginError",
    "PluginLoader",
    "PluginManager",
    "PluginManifest",
    "PluginMetadata",
    "PluginRegistry",
    "PluginState",
    "PluginLoadError",
    "validate_dependencies",
    "version_in_range",
]
