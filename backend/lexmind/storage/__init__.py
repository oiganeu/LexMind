"""Storage Abstraction Layer.

This package provides a backend-agnostic interface for all file
storage in LexMind.  Higher layers (workspace, artifacts, ingestion)
interact with storage exclusively through ``StorageManager``.

Quick start::

    from pathlib import Path
    from lexmind.storage import StorageManager, FilesystemStorageProvider

    provider = FilesystemStorageProvider(Path("/data/storage"))
    manager = StorageManager(provider)

    manager.save("storage://ws/docs/file.pdf", b"...")
    data = manager.load("storage://ws/docs/file.pdf")

Architecture::

    Application / Workspace / Artifacts
                |
          StorageManager          (façade -- URI-based API)
                |
          StorageProvider         (Protocol -- path-based)
                |
          FilesystemStorageProvider  (concrete -- pathlib only)
"""

from lexmind.storage.exceptions import (
    InvalidStorageURIError,
    StorageAlreadyExistsError,
    StorageChecksumError,
    StorageError,
    StorageNotFoundError,
    StoragePermissionDeniedError,
)
from lexmind.storage.filesystem import FilesystemStorageProvider
from lexmind.storage.manager import StorageManager
from lexmind.storage.models import StorageObject, StorageStat, compute_checksum
from lexmind.storage.types import ContentType, StorageBackend
from lexmind.storage.uri import StorageURI, build_uri, join_uri, parse_uri

__all__ = [
    # Exceptions
    "InvalidStorageURIError",
    "StorageAlreadyExistsError",
    "StorageChecksumError",
    "StorageError",
    "StorageNotFoundError",
    "StoragePermissionDeniedError",
    # Provider
    "FilesystemStorageProvider",
    # Manager
    "StorageManager",
    # Models
    "StorageObject",
    "StorageStat",
    "compute_checksum",
    # Types
    "ContentType",
    "StorageBackend",
    # URI
    "StorageURI",
    "build_uri",
    "join_uri",
    "parse_uri",
]
