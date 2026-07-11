"""Metadata describing a LexMind module."""

from dataclasses import dataclass, field
from typing import Any

from lexmind.core.capabilities import Capability


@dataclass(frozen=True)
class ModuleMetadata:
    """Immutable metadata for a module."""

    name: str
    author: str = "Unknown"
    version: str = "0.0.0"
    license: str = "Apache-2.0"
    website: str = ""
    description: str = ""
    supported_platforms: tuple[str, ...] = field(default_factory=tuple)
    experimental: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def has_capability(self, capability: Capability) -> bool:
        """Return True if this metadata advertises a capability."""
        return capability in self.extra.get("capabilities", ())
