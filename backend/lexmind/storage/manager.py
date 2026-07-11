"""StorageManager -- the single entry point for all storage operations.

Higher layers (workspace, artifacts, ingestion) interact with storage
exclusively through this façade.  The manager delegates to a
``StorageProvider`` and translates between URI-based public API and
the provider's path-based interface.

Architecture::

    Application
        |
    StorageManager  <-- you are here
        |
    StorageProvider (abstract)
        |
    FilesystemStorageProvider / S3 / etc.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

from lexmind.storage.models import StorageStat
from lexmind.storage.uri import parse_uri

logger = logging.getLogger(__name__)


class StorageManager:
    """Façade that routes storage operations to the correct provider.

    All public methods accept **storage URIs** (``storage://...``).
    The manager strips the scheme and delegates the relative path
    to the underlying ``StorageProvider``.

    Usage::

        fs = FilesystemStorageProvider(Path("/data"))
        mgr = StorageManager(provider=fs)
        mgr.save("storage://ws/docs/file.pdf", b"...")
    """

    def __init__(self, provider: StorageProvider) -> None:  # noqa: F821
        """Initialise with a concrete storage provider.

        Args:
            provider: Any object satisfying the ``StorageProvider``
                      Protocol.
        """
        self._provider = provider
        logger.info(
            "storage_manager_init",
            backend=provider.backend_name,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_path(self, uri: str) -> str:
        """Strip the scheme and return the relative path from the URI.

        Raises InvalidStorageURIError for malformed URIs.
        """
        parsed = parse_uri(uri)
        return parsed.path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(self, uri: str, data: bytes) -> None:
        """Write *data* to the object identified by *uri*.

        Args:
            uri: A storage URI.
            data: Raw bytes to write.
        """
        path = self._extract_path(uri)
        logger.debug("storage_save", uri=uri, size=len(data))
        self._provider.write_bytes(path, data)

    def load(self, uri: str) -> bytes:
        """Read and return the raw bytes at *uri*.

        Args:
            uri: A storage URI.

        Returns:
            The raw bytes.

        Raises:
            StorageNotFoundError: If the object does not exist.
        """
        path = self._extract_path(uri)
        logger.debug("storage_load", uri=uri)
        return self._provider.read_bytes(path)

    def load_text(self, uri: str, encoding: str = "utf-8") -> str:
        """Read *uri* and return decoded text.

        Args:
            uri: A storage URI.
            encoding: Character encoding (default utf-8).

        Returns:
            The decoded text content.
        """
        path = self._extract_path(uri)
        return self._provider.read_text(path, encoding=encoding)

    def save_text(
        self, uri: str, text: str, encoding: str = "utf-8"
    ) -> None:
        """Write *text* to the object identified by *uri*.

        Args:
            uri: A storage URI.
            text: Text content to write.
            encoding: Character encoding (default utf-8).
        """
        path = self._extract_path(uri)
        self._provider.write_text(path, text, encoding=encoding)

    def delete(self, uri: str) -> None:
        """Delete the object at *uri*.

        Args:
            uri: A storage URI.

        Raises:
            StorageNotFoundError: If the object does not exist.
        """
        path = self._extract_path(uri)
        logger.debug("storage_delete", uri=uri)
        self._provider.delete(path)

    def copy(self, src_uri: str, dst_uri: str) -> None:
        """Copy an object from *src_uri* to *dst_uri*.

        Args:
            src_uri: Source storage URI.
            dst_uri: Destination storage URI.
        """
        src_path = self._extract_path(src_uri)
        dst_path = self._extract_path(dst_uri)
        logger.debug("storage_copy", src=src_uri, dst=dst_uri)
        self._provider.copy(src_path, dst_path)

    def move(self, src_uri: str, dst_uri: str) -> None:
        """Move an object from *src_uri* to *dst_uri*.

        Args:
            src_uri: Source storage URI.
            dst_uri: Destination storage URI.
        """
        src_path = self._extract_path(src_uri)
        dst_path = self._extract_path(dst_uri)
        logger.debug("storage_move", src=src_uri, dst=dst_uri)
        self._provider.move(src_path, dst_path)

    def checksum(
        self, uri: str, algorithm: str = "sha256"
    ) -> str:
        """Compute and return the hex digest checksum of *uri*.

        Args:
            uri: A storage URI.
            algorithm: Hash algorithm (default sha256).

        Returns:
            Hex-encoded checksum string.
        """
        path = self._extract_path(uri)
        return self._provider.checksum(path, algorithm=algorithm)

    def exists(self, uri: str) -> bool:
        """Return True if the object at *uri* exists.

        Args:
            uri: A storage URI.
        """
        path = self._extract_path(uri)
        return self._provider.exists(path)

    def stat(self, uri: str) -> StorageStat:
        """Return stat information for *uri*.

        Args:
            uri: A storage URI.

        Returns:
            A StorageStat instance.
        """
        path = self._extract_path(uri)
        return self._provider.stat(path)

    def list(self, uri: str = "") -> list[str]:
        """Return immediate children of *uri*.

        Args:
            uri: A storage URI pointing to a directory.  Defaults
                 to the storage root.

        Returns:
            List of child names.
        """
        path = self._extract_path(uri) if uri else ""
        return self._provider.list(path)

    def mkdir(self, uri: str) -> None:
        """Create a directory at *uri*.

        Args:
            uri: A storage URI.
        """
        path = self._extract_path(uri)
        self._provider.mkdir(path)

    def walk(
        self, uri: str = ""
    ) -> Iterator[tuple[str, list[str], list[str]]]:
        """Walk the directory tree rooted at *uri*.

        Yields (dirpath, dirnames, filenames) tuples.
        """
        path = self._extract_path(uri) if uri else ""
        yield from self._provider.walk(path)

    @property
    def backend(self) -> str:
        """Return the backend name of the underlying provider."""
        return self._provider.backend_name

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"StorageManager(backend={self._provider.backend_name!r})"
