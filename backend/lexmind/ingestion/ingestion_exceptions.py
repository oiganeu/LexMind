"""Ingestion exceptions."""

from lexmind.exceptions import LexMindError


class IngestionError(LexMindError):
    """Base class for ingestion errors."""


class UnsupportedFileTypeError(IngestionError):
    """Raised when a file type is not supported by the ingestion engine."""


class InvalidPathError(IngestionError):
    """Raised when a source path is invalid or unsafe."""


class DuplicateFileError(IngestionError):
    """Raised when a duplicate file is detected and duplicates are rejected."""


class JobNotFoundError(IngestionError):
    """Raised when an ingestion job cannot be located."""


class InvalidJobStateError(IngestionError):
    """Raised when an operation is invalid for the current job state."""


class DiscoveryError(IngestionError):
    """Raised when file discovery fails."""
