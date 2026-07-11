"""Ingestion source interfaces.

Defines the contract every source (filesystem, workspace, and future
remote sources such as S3, WebDAV, SharePoint, Google Drive, Nextcloud,
and network shares) must satisfy. Only the filesystem source is
implemented in this framework task.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Protocol, runtime_checkable

from lexmind.ingestion.ingestion_result import DiscoveredFile


@runtime_checkable
class IngestionSource(Protocol):
    """Contract for a source that yields ingestible files."""

    @property
    def name(self) -> str:
        """A stable identifier for the source type."""
        ...

    def discover(self, location: str, recursive: bool = True) -> Iterator[DiscoveredFile]:
        """Yield discovered files from the given location."""
        ...

    def open_bytes(self, path: Path) -> bytes:
        """Return the raw bytes of a discovered file."""
        ...
