"""Filesystem file discovery."""

from collections.abc import Iterator
from pathlib import Path

from lexmind.ingestion.ingestion_exceptions import DiscoveryError
from lexmind.ingestion.ingestion_result import DiscoveredFile
from lexmind.ingestion.mime_detector import MimeDetector


class FileDiscovery:
    """Discovers files on the local filesystem (a filesystem source)."""

    name = "filesystem"

    def __init__(self, mime_detector: MimeDetector | None = None) -> None:
        self._mime = mime_detector or MimeDetector()

    def discover(self, location: str, recursive: bool = True) -> Iterator[DiscoveredFile]:
        """Yield files found under ``location``.

        If ``location`` is a single file, that file is yielded. If it is a
        directory, its files are yielded recursively by default.
        """
        root = Path(location)
        if not root.exists():
            raise DiscoveryError(f"Location does not exist: '{root}'.")
        if root.is_file():
            yield self._describe(root)
            return
        pattern = "**/*" if recursive else "*"
        for entry in sorted(root.glob(pattern)):
            if entry.is_file():
                yield self._describe(entry)

    def open_bytes(self, path: Path) -> bytes:
        """Return the raw bytes of a discovered file."""
        return Path(path).read_bytes()

    def _describe(self, path: Path) -> DiscoveredFile:
        mime_type, category = self._mime.detect(path)
        return DiscoveredFile(
            path=path,
            size_bytes=path.stat().st_size,
            mime_type=mime_type,
            category=category,
        )
