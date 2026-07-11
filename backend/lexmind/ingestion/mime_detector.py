"""MIME type detection based on file extension.

Content-based sniffing is a future extension. This module only maps known
extensions to MIME types and reports supported file categories.
"""

from enum import StrEnum
from pathlib import Path


class FileCategory(StrEnum):
    """High-level category of an ingestible file."""

    DOCUMENT = "document"
    IMAGE = "image"
    EMAIL = "email"
    AUDIO = "audio"
    VIDEO = "video"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"


# Extension to (mime type, category, currently supported).
_EXTENSION_MAP: dict[str, tuple[str, FileCategory, bool]] = {
    ".pdf": ("application/pdf", FileCategory.DOCUMENT, True),
    ".docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        FileCategory.DOCUMENT,
        True,
    ),
    ".odt": ("application/vnd.oasis.opendocument.text", FileCategory.DOCUMENT, True),
    ".txt": ("text/plain", FileCategory.DOCUMENT, True),
    ".rtf": ("application/rtf", FileCategory.DOCUMENT, True),
    ".html": ("text/html", FileCategory.DOCUMENT, True),
    ".htm": ("text/html", FileCategory.DOCUMENT, True),
    ".eml": ("message/rfc822", FileCategory.EMAIL, True),
    ".msg": ("application/vnd.ms-outlook", FileCategory.EMAIL, True),
    ".png": ("image/png", FileCategory.IMAGE, True),
    ".jpg": ("image/jpeg", FileCategory.IMAGE, True),
    ".jpeg": ("image/jpeg", FileCategory.IMAGE, True),
    ".tif": ("image/tiff", FileCategory.IMAGE, True),
    ".tiff": ("image/tiff", FileCategory.IMAGE, True),
    ".bmp": ("image/bmp", FileCategory.IMAGE, True),
    ".webp": ("image/webp", FileCategory.IMAGE, True),
    ".mp3": ("audio/mpeg", FileCategory.AUDIO, False),
    ".wav": ("audio/wav", FileCategory.AUDIO, False),
    ".mp4": ("video/mp4", FileCategory.VIDEO, False),
    ".mkv": ("video/x-matroska", FileCategory.VIDEO, False),
    ".zip": ("application/zip", FileCategory.ARCHIVE, False),
}


class MimeDetector:
    """Resolves MIME type and category from a file path."""

    def detect(self, path: Path) -> tuple[str, FileCategory]:
        """Return the (mime_type, category) for the given path."""
        entry = _EXTENSION_MAP.get(Path(path).suffix.lower())
        if entry is None:
            return "application/octet-stream", FileCategory.UNKNOWN
        return entry[0], entry[1]

    def is_supported(self, path: Path) -> bool:
        """Return True if the file type is currently supported for import."""
        entry = _EXTENSION_MAP.get(Path(path).suffix.lower())
        return bool(entry and entry[2])

    def is_known(self, path: Path) -> bool:
        """Return True if the extension is known (supported now or future)."""
        return Path(path).suffix.lower() in _EXTENSION_MAP
