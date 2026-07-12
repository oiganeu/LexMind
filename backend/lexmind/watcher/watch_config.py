"""Watch configuration value object."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


def _normalize_patterns(patterns: set[str]) -> frozenset[str]:
    """Normalize file-type patterns to lower-case extensions.

    Each entry is forced to a lower-case extension beginning with a
    dot (``".pdf"``).  Entries without a leading dot are accepted and
    also normalised (``"pdf"`` becomes ``".pdf"``).
    """
    normalized: set[str] = set()
    for pattern in patterns:
        value = pattern.strip().lower()
        if not value:
            continue
        if not value.startswith("."):
            value = f".{value}"
        normalized.add(value)
    return frozenset(normalized)


@dataclass(frozen=True, slots=True)
class WatchConfig:
    """Immutable description of a single watch subscription.

    Attributes:
        watch_id: Unique identifier for this watch.
        workspace_id: Workspace that owns the watched location.
        root_uri: Storage URI of the directory to monitor.
        patterns: Allowed file extensions (e.g. ``{".pdf", ".png"}``).
            An empty set accepts every file type.
        recursive: Whether subdirectories are monitored.
        debounce_seconds: Minimum quiet period (seconds) before a
            burst of changes to the same file is emitted as a single
            event.  ``0`` disables debouncing.
        enabled: Whether the watch is active.
    """

    watch_id: str
    workspace_id: str
    root_uri: str
    patterns: frozenset[str] = frozenset()
    recursive: bool = True
    debounce_seconds: float = 0.0
    enabled: bool = True

    def __post_init__(self) -> None:
        """Normalize pattern extensions and validate the config."""
        object.__setattr__(self, "patterns", _normalize_patterns(self.patterns))
        if self.debounce_seconds < 0:
            raise ValueError("debounce_seconds must be non-negative")
        if not self.root_uri:
            raise ValueError("root_uri must not be empty")

    @property
    def extension_filter(self) -> frozenset[str]:
        """Return the normalized lower-case extension filter."""
        return self.patterns

    def accepts_extension(self, uri: str) -> bool:
        """Return True when *uri* matches the configured patterns."""
        if not self.patterns:
            return True
        return PurePosixPath(uri).suffix.lower() in self.patterns
