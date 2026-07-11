"""Path validation for ingestion sources."""

from pathlib import Path

from lexmind.ingestion.ingestion_exceptions import InvalidPathError


class PathValidator:
    """Validates that source paths are safe and readable.

    An optional ``allowed_root`` constrains imports to a directory subtree,
    preventing traversal outside the permitted workspace.
    """

    def __init__(self, allowed_root: Path | None = None) -> None:
        self._allowed_root = Path(allowed_root).resolve() if allowed_root else None

    def validate(self, path: Path) -> Path:
        """Return the resolved path or raise ``InvalidPathError``."""
        candidate = Path(path)
        try:
            resolved = candidate.resolve()
        except OSError as exc:
            raise InvalidPathError(f"Cannot resolve path '{path}': {exc}") from exc
        if not resolved.exists():
            raise InvalidPathError(f"Path does not exist: '{resolved}'.")
        if self._allowed_root is not None and not self._is_within_root(resolved):
            raise InvalidPathError(
                f"Path '{resolved}' is outside the allowed root '{self._allowed_root}'."
            )
        return resolved

    def _is_within_root(self, resolved: Path) -> bool:
        if self._allowed_root is None:
            return True
        return self._allowed_root == resolved or self._allowed_root in resolved.parents
