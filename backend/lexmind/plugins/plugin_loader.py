"""Plugin loader skeleton.

Provides the structure for loading plugins from entry points or modules.
The concrete loading logic (importlib machinery) is intentionally minimal
— only the contract and validation are implemented here. Future versions
will support hot reload and remote registries.
"""

import importlib
from typing import Any

from lexmind.plugins.plugin_exceptions import PluginLoadError
from lexmind.plugins.plugin_manifest import PluginManifest


class PluginLoader:
    """Loads plugin objects from a declared entrypoint."""

    def load_entrypoint(self, entrypoint: str) -> Any:
        """Import ``entrypoint`` and return the referenced object.

        The entrypoint is a dotted path ``module:attribute`` pointing to a
        callable or plugin class.
        """
        if ":" not in entrypoint:
            raise PluginLoadError(
                f"Invalid entrypoint '{entrypoint}'; expected 'module:attribute'."
            )
        module_name, attr = entrypoint.split(":", 1)
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            raise PluginLoadError(f"Failed to import module '{module_name}': {exc}") from exc
        if not hasattr(module, attr):
            raise PluginLoadError(f"Module '{module_name}' has no attribute '{attr}'.")
        return getattr(module, attr)

    def load_from_manifest(self, manifest: PluginManifest) -> Any:
        """Load the plugin object declared by a manifest."""
        if not manifest.entrypoint:
            raise PluginLoadError(f"Manifest '{manifest.id}' has no entrypoint.")
        return self.load_entrypoint(manifest.entrypoint)
