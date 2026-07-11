"""Storage URI parser and builder.

Handles URIs in the form::

    storage://workspace/documents/file.pdf
    storage://workspace/artifacts/abc123/meta.json

The scheme ``storage://`` identifies LexMind storage URIs.
The first path segment is the *authority* (typically the workspace ID).
The remaining path is the *relative path* within that workspace.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from lexmind.storage.exceptions import InvalidStorageURIError

SCHEME = "storage"


@dataclass(frozen=True)
class StorageURI:
    """Parsed representation of a storage URI.

    Attributes:
        workspace: The workspace or authority identifier.
        path: The relative path within the workspace (posix separators).
        raw: The original unparsed URI string.
    """

    workspace: str
    path: str
    raw: str

    @property
    def parent(self) -> StorageURI:
        """Return the parent URI (one directory up)."""
        parent_path = str(PurePosixPath(self.path).parent)
        if parent_path == ".":
            parent_path = ""
        return StorageURI(
            workspace=self.workspace,
            path=parent_path,
            raw=self.raw,
        )

    @property
    def name(self) -> str:
        """Return the filename component."""
        return PurePosixPath(self.path).name

    @property
    def suffix(self) -> str:
        """Return the file extension including the dot."""
        return PurePosixPath(self.path).suffix

    def child(self, name: str) -> StorageURI:
        """Return a new URI with *name* appended as a child path."""
        child_path = str(PurePosixPath(self.path) / name)
        return StorageURI(
            workspace=self.workspace,
            path=child_path,
            raw=f"{SCHEME}://{self.workspace}/{child_path}",
        )

    def __str__(self) -> str:
        """Return the full URI string."""
        return f"{SCHEME}://{self.workspace}/{self.path}"


def parse_uri(uri: str) -> StorageURI:
    """Parse a storage URI string into a StorageURI object.

    Args:
        uri: A URI string in the form ``storage://workspace/path``.

    Returns:
        A parsed StorageURI instance.

    Raises:
        InvalidStorageURIError: If the URI is malformed.
    """
    if not uri:
        raise InvalidStorageURIError(uri, "empty URI")

    if not uri.startswith(f"{SCHEME}://"):
        raise InvalidStorageURIError(
            uri, f"scheme must be '{SCHEME}://'"
        )

    remainder = uri[len(f"{SCHEME}://"):]
    if not remainder:
        raise InvalidStorageURIError(uri, "missing workspace")

    parts = remainder.split("/", 1)
    workspace = parts[0]
    if not workspace:
        raise InvalidStorageURIError(uri, "empty workspace")

    path = parts[1] if len(parts) > 1 else ""

    return StorageURI(workspace=workspace, path=path, raw=uri)


def build_uri(workspace: str, path: str) -> str:
    """Build a storage URI string from workspace and path.

    Args:
        workspace: The workspace identifier.
        path: The relative path within the workspace.

    Returns:
        A fully-qualified storage URI string.
    """
    clean_path = str(PurePosixPath(path)) if path else ""
    return f"{SCHEME}://{workspace}/{clean_path}"


def join_uri(base: str, *segments: str) -> str:
    """Join a base storage URI with path segments.

    Args:
        base: A base storage URI string.
        *segments: Additional path segments to append.

    Returns:
        The joined storage URI string.
    """
    parsed = parse_uri(base)
    current = PurePosixPath(parsed.path)
    for segment in segments:
        current = current / segment
    return build_uri(parsed.workspace, str(current))
