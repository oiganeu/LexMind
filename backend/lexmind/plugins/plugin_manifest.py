"""Plugin manifest model and parsing.

A manifest is the declarative description of a plugin, typically loaded
from a ``plugin.yaml`` file. This module provides parsing from both dict
and YAML text without depending on a concrete plugin implementation.
"""

from dataclasses import dataclass, field
from typing import Any

from lexmind.plugins.plugin_capability import PluginCapability


@dataclass(frozen=True)
class PluginManifest:
    """Declarative description of a plugin."""

    id: str
    version: str
    author: str = "Unknown"
    description: str = ""
    license: str = "Apache-2.0"
    homepage: str = ""
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    permissions: tuple[str, ...] = field(default_factory=tuple)
    capabilities: tuple[PluginCapability, ...] = field(default_factory=tuple)
    entrypoint: str = ""
    minimum_kernel_version: str | None = None
    maximum_kernel_version: str | None = None
    experimental: bool = False
    enabled: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginManifest":
        """Build a manifest from a dictionary."""

        def _tuple(value: Any) -> tuple[str, ...]:
            if value is None:
                return ()
            if isinstance(value, str):
                return (value,)
            return tuple(str(v) for v in value)

        def _caps(value: Any) -> tuple[PluginCapability, ...]:
            return tuple(PluginCapability(str(c)) for c in _tuple(value))

        return cls(
            id=str(data["id"]),
            version=str(data["version"]),
            author=str(data.get("author", "Unknown")),
            description=str(data.get("description", "")),
            license=str(data.get("license", "Apache-2.0")),
            homepage=str(data.get("homepage", "")),
            dependencies=_tuple(data.get("dependencies")),
            permissions=_tuple(data.get("permissions")),
            capabilities=_caps(data.get("capabilities")),
            entrypoint=str(data.get("entrypoint", "")),
            minimum_kernel_version=data.get("minimum_kernel_version"),
            maximum_kernel_version=data.get("maximum_kernel_version"),
            experimental=bool(data.get("experimental", False)),
            enabled=bool(data.get("enabled", True)),
            extra={k: v for k, v in data.items() if k not in _KNOWN_FIELDS},
        )

    @classmethod
    def from_yaml(cls, text: str) -> "PluginManifest":
        """Build a manifest from YAML text."""
        import yaml

        return cls.from_dict(yaml.safe_load(text) or {})


_KNOWN_FIELDS = frozenset(
    {
        "id",
        "version",
        "author",
        "description",
        "license",
        "homepage",
        "dependencies",
        "permissions",
        "capabilities",
        "entrypoint",
        "minimum_kernel_version",
        "maximum_kernel_version",
        "experimental",
        "enabled",
    }
)
