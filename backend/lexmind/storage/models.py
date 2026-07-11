"""Storage domain models."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import PurePosixPath

from lexmind.storage.types import ContentType, StorageBackend


@dataclass(frozen=True)
class StorageObject:
    """Immutable description of a stored object.

    This is the public-facing representation of a storage entry.
    Internal paths are never leaked outside the provider.
    """

    uri: str
    size: int
    created: datetime
    modified: datetime
    checksum: str
    backend: StorageBackend
    content_type: ContentType = ContentType.UNKNOWN
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def name(self) -> str:
        """Return the filename component of the URI."""
        return PurePosixPath(self.uri).name

    @property
    def parent(self) -> str:
        """Return the parent URI (one path segment up)."""
        if self.uri.startswith("storage://"):
            remainder = self.uri[len("storage://"):]
            parts = remainder.split("/", 1)
            workspace = parts[0]
            rel = parts[1] if len(parts) > 1 else ""
            parent_rel = str(PurePosixPath(rel).parent)
            if parent_rel == ".":
                parent_rel = ""
            return f"storage://{workspace}/{parent_rel}"
        return str(PurePosixPath(self.uri).parent)

    @property
    def extension(self) -> str:
        """Return the file extension (including the dot)."""
        return PurePosixPath(self.uri).suffix

    @property
    def is_root(self) -> bool:
        """Return True if this URI points to a root directory."""
        return self.uri == "/" or self.uri == ""


@dataclass(frozen=True)
class StorageStat:
    """Lightweight stat information about a storage object."""

    exists: bool
    is_directory: bool = False
    size: int = 0
    modified: datetime | None = None


def compute_checksum(data: bytes, algorithm: str = "sha256") -> str:
    """Compute hex digest checksum for raw bytes.

    Args:
        data: Raw bytes to hash.
        algorithm: Hash algorithm name (default sha256).

    Returns:
        Hex-encoded checksum string.

    Raises:
        ValueError: If the algorithm is not supported.
    """
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as exc:
        msg = f"Unsupported hash algorithm: {algorithm}"
        raise ValueError(msg) from exc
    hasher.update(data)
    return hasher.hexdigest()


def utcnow() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(UTC)
