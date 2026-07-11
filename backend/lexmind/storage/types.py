"""Storage backend type enumerations."""

from enum import Enum, unique


@unique
class StorageBackend(Enum):
    """Supported storage backends.

    Each value identifies a concrete StorageProvider implementation.
    """

    FILESYSTEM = "filesystem"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"
    NFS = "nfs"


@unique
class ContentType(Enum):
    """Common content types for stored objects."""

    UNKNOWN = "application/octet-stream"
    PDF = "application/pdf"
    PLAIN_TEXT = "text/plain"
    MARKDOWN = "text/markdown"
    JSON = "application/json"
    XML = "application/xml"
    HTML = "text/html"
    PNG = "image/png"
    JPEG = "image/jpeg"
    TIFF = "image/tiff"
    CSV = "text/csv"
