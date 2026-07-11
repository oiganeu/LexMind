"""Filesystem-backed storage provider.

All filesystem access is encapsulated here.  Higher layers must
never import ``pathlib`` or ``os`` for storage operations; they
go through ``StorageManager`` which delegates to this provider.

Constraints:
    - Uses ``pathlib.Path`` exclusively.
    - Never exposes absolute host paths outside the provider.
    - Never uses ``os.path``.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from lexmind.storage.exceptions import (
    StorageNotFoundError,
    StoragePermissionDeniedError,
)
from lexmind.storage.models import StorageStat, compute_checksum, utcnow
from lexmind.storage.types import StorageBackend


class FilesystemStorageProvider:
    """Concrete storage provider backed by the local filesystem.

    All *path* arguments are **relative** to ``root``.  The provider
    resolves them to absolute ``pathlib.Path`` instances internally.
    """

    def __init__(self, root: Path) -> None:
        """Initialise the provider with a root directory.

        Args:
            root: The absolute path to the storage root.  Created
                  if it does not exist.

        Raises:
            ValueError: If *root* is not an absolute path.
        """
        if not root.is_absolute():
            msg = f"Root must be an absolute path, got: {root}"
            raise ValueError(msg)
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve(self, rel: str) -> Path:
        """Resolve a relative path against the root.

        Raises StoragePermissionDeniedError for path traversal attacks.
        """
        resolved = (self._root / rel).resolve()
        if not str(resolved).startswith(str(self._root.resolve())):
            msg = f"Path traversal not allowed: {rel}"
            raise StoragePermissionDeniedError(msg, "resolve")
        return resolved

    def _require_exists(self, path: str) -> Path:
        """Resolve and assert the object exists."""
        resolved = self._resolve(path)
        if not resolved.exists():
            raise StorageNotFoundError(path)
        return resolved

    # ------------------------------------------------------------------
    # StorageProvider interface
    # ------------------------------------------------------------------

    @property
    def backend_name(self) -> str:
        """Return a human-readable backend identifier."""
        return StorageBackend.FILESYSTEM.value

    def exists(self, path: str) -> bool:
        """Return True if *path* exists in the backend."""
        return self._resolve(path).exists()

    def read_bytes(self, path: str) -> bytes:
        """Read and return the raw bytes at *path*."""
        resolved = self._require_exists(path)
        if resolved.is_dir():
            raise StorageNotFoundError(path)
        return resolved.read_bytes()

    def write_bytes(self, path: str, data: bytes) -> None:
        """Write *data* to *path*, creating parent dirs as needed."""
        resolved = self._resolve(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_bytes(data)

    def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read *path* and return decoded text."""
        resolved = self._require_exists(path)
        if resolved.is_dir():
            raise StorageNotFoundError(path)
        return resolved.read_text(encoding=encoding)

    def write_text(
        self, path: str, text: str, encoding: str = "utf-8"
    ) -> None:
        """Write *text* to *path*, creating parent dirs as needed."""
        resolved = self._resolve(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(text, encoding=encoding)

    def delete(self, path: str) -> None:
        """Delete the object at *path*.

        Raises StorageNotFoundError if *path* does not exist.
        """
        resolved = self._require_exists(path)
        if resolved.is_dir():
            import shutil
            shutil.rmtree(resolved)
        else:
            resolved.unlink()

    def copy(self, src: str, dst: str) -> None:
        """Copy an object from *src* to *dst*.

        Raises:
            StorageNotFoundError: If *src* does not exist.
        """
        src_path = self._require_exists(src)
        dst_path = self._resolve(dst)
        if src_path.is_dir():
            import shutil
            shutil.copytree(src_path, dst_path)
        else:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(src_path, dst_path)

    def move(self, src: str, dst: str) -> None:
        """Move an object from *src* to *dst*.

        Raises:
            StorageNotFoundError: If *src* does not exist.
        """
        src_path = self._require_exists(src)
        dst_path = self._resolve(dst)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.move(str(src_path), str(dst_path))

    def mkdir(self, path: str, parents: bool = True) -> None:
        """Create a directory at *path*."""
        resolved = self._resolve(path)
        resolved.mkdir(parents=parents, exist_ok=True)

    def list(self, path: str = "") -> list[str]:
        """Return immediate children of *path* (names only)."""
        resolved = self._resolve(path)
        if not resolved.exists():
            raise StorageNotFoundError(path)
        if not resolved.is_dir():
            raise StorageNotFoundError(path)
        return sorted(entry.name for entry in resolved.iterdir())

    def walk(
        self, path: str = ""
    ) -> Iterator[tuple[str, list[str], list[str]]]:
        """Walk the directory tree rooted at *path*.

        Yields (dirpath, dirnames, filenames) tuples.  Paths are
        relative to the provider root.
        """
        root = self._resolve(path)
        if not root.exists():
            raise StorageNotFoundError(path)
        for dirpath, dirnames, filenames in root.walk():
            rel = str(dirpath.relative_to(self._root))
            if rel == ".":
                rel = ""
            dirnames.sort()
            filenames.sort()
            yield rel, dirnames, filenames

    def stat(self, path: str) -> StorageStat:
        """Return stat information for *path*."""
        resolved = self._resolve(path)
        if not resolved.exists():
            return StorageStat(exists=False)
        return StorageStat(
            exists=True,
            is_directory=resolved.is_dir(),
            size=resolved.stat().st_size if resolved.is_file() else 0,
            modified=utcnow(),
        )

    def checksum(
        self, path: str, algorithm: str = "sha256"
    ) -> str:
        """Compute and return the hex digest checksum of *path*."""
        data = self.read_bytes(path)
        return compute_checksum(data, algorithm=algorithm)

    def open(  # noqa: A003
        self, path: str, mode: str = "rb"
    ) -> object:
        """Open *path* and return a file-like object.

        The caller must close the returned handle.
        """
        resolved = self._resolve(path)
        if "w" in mode or "a" in mode or "x" in mode:
            resolved.parent.mkdir(parents=True, exist_ok=True)
        return resolved.open(mode)

    def resolve(self, path: str) -> Path:
        """Resolve *path* to an absolute backend-specific path.

        This is an implementation detail and must not be exposed
        outside the provider boundary.
        """
        return self._resolve(path)

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"FilesystemStorageProvider(root={self._root!s})"
