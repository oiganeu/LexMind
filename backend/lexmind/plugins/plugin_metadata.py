"""Plugin metadata."""

from dataclasses import dataclass, field
from typing import Any

from lexmind.plugins.plugin_capability import PluginCapability


@dataclass(frozen=True)
class PluginMetadata:
    """Immutable metadata describing a plugin."""

    id: str
    name: str
    version: str
    display_name: str = ""
    author: str = "Unknown"
    license: str = "Apache-2.0"
    homepage: str = ""
    repository: str = ""
    description: str = ""
    capabilities: tuple[PluginCapability, ...] = field(default_factory=tuple)
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    supported_platforms: tuple[str, ...] = field(default_factory=tuple)
    minimum_kernel_version: str | None = None
    maximum_kernel_version: str | None = None
    experimental: bool = False
    enabled: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def is_compatible_kernel(self, kernel_version: str) -> bool:
        """Return True if the kernel version satisfies declared bounds."""
        from lexmind.plugins.plugin_manager import version_in_range

        return version_in_range(
            kernel_version,
            self.minimum_kernel_version,
            self.maximum_kernel_version,
        )
