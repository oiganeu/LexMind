"""Plugin discovery skeleton.

Supports filesystem discovery (scanning directories for ``plugin.yaml``)
and namespace packages. Concrete scanning is intentionally minimal; the
API is stable for future pip packages and remote registries.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lexmind.plugins.plugin_manifest import PluginManifest


@dataclass
class PluginCandidate:
    """A discovered plugin before loading."""

    path: Path
    manifest: PluginManifest | None = None


class Discovery:
    """Discovers plugin candidates on the filesystem."""

    def scan_directory(self, root: Path) -> list[PluginCandidate]:
        """Return candidates by locating ``plugin.yaml`` files under root."""
        candidates: list[PluginCandidate] = []
        for manifest_path in Path(root).rglob("plugin.yaml"):
            manifest = PluginManifest.from_yaml(manifest_path.read_text())
            candidates.append(PluginCandidate(path=manifest_path, manifest=manifest))
        return candidates

    def discover_namespace(self, package_name: str) -> list[Any]:
        """Discover plugins exposed via a namespace package.

        Placeholder for future namespace-based discovery.
        """
        import importlib

        try:
            importlib.import_module(package_name)
        except ImportError:
            return []
        return []
