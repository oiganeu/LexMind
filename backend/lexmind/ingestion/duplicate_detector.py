"""Duplicate detection based on content checksums."""


class DuplicateDetector:
    """Tracks seen checksums to identify duplicate files within a run.

    The detector is stateful per ingestion job. A persistent, cross-session
    store is a future extension backed by a repository.
    """

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def is_duplicate(self, checksum: str) -> bool:
        """Return True if the checksum has already been seen."""
        return checksum in self._seen

    def register(self, checksum: str) -> None:
        """Record a checksum as seen."""
        self._seen.add(checksum)

    def check_and_register(self, checksum: str) -> bool:
        """Return True if duplicate; otherwise register and return False."""
        if checksum in self._seen:
            return True
        self._seen.add(checksum)
        return False

    def reset(self) -> None:
        """Clear all tracked checksums."""
        self._seen.clear()

    @property
    def count(self) -> int:
        """Number of unique checksums tracked."""
        return len(self._seen)
