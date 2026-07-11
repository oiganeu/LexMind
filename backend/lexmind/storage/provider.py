"""Abstract storage provider interface.

Every concrete storage backend (filesystem, S3, NFS, ...) must
implement this Protocol.  Higher layers interact only through
``StorageManager`` and never call a provider directly.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Protocol, runtime_checkable

from lexmind.storage.models import StorageStat


@runtime_checkable
class StorageProvider(Protocol):
    """Protocol that all storage backends must satisfy.

    Path arguments are **relative** to the provider root.
    The provider is responsible for resolving them to an
    absolute backend-specific location.
    """

    def exists(self, path: str) -> bool:
        """Return True if *path* exists in the backend."""
        ...

    def read_bytes(self, path: str) -> bytes:
        """Read and return the raw bytes at *path*."""
        ...

    def write_bytes(self, path: str, data: bytes) -> None:
        """Write *data* to *path*, creating parent dirs as needed."""
        ...

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read *path* and return decoded text."""
        ...

    def write_text(
        self, path: str, text: str, encoding: str = "utf-8"
    ) -> None:
        """Write *text* to *path*, creating parent dirs as needed."""
        ...

    def delete(self, path: str) -> None:
        """Delete the object at *path*."""
        ...

    def copy(self, src: str, dst: str) -> None:
        """Copy an object from *src* to *dst*."""
        ...

    def move(self, src: str, dst: str) -> None:
        """Move an object from *src* to *dst*."""
        ...

    def mkdir(self, path: str, parents: bool = True) -> None:
        """Create a directory at *path*."""
        ...

    def list(self, path: str = "") -> list[str]:
        """Return immediate children of *path* (names only)."""
        ...

    def walk(self, path: str = "") -> Iterator[tuple[str, list[str], list[str]]]:
        """Walk the directory tree rooted at *path*.

        Yields (dirpath, dirnames, filenames) like pathlib.Path.walk().
        """
        ...

    def stat(self, path: str) -> StorageStat:
        """Return stat information for *path*."""
        ...

    def checksum(self, path: str, algorithm: str = "sha256") -> str:
        """Compute and return the hex digest checksum of *path*."""
        ...

    def open(
        self, path: str, mode: str = "rb"
    ) -> SupportsClose:  # noqa: F821
        """Open *path* and return a file-like object.

        The caller is responsible for closing the returned handle.
        """
        ...

    def resolve(self, path: str) -> Path:
        """Resolve *path* to an absolute backend-specific path.

        The returned Path is an **implementation detail** and
        must never be exposed outside the provider.
        """
        ...

    @property
    def backend_name(self) -> str:
        """Return a human-readable backend identifier."""
        ...
