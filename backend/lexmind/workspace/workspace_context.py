"""Workspace context -- runtime dependencies exposed to plugins."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EventBus(Protocol):
    """Minimal event bus interface for publishing domain events."""

    def publish(self, event: object) -> None:
        """Publish *event* to all subscribers."""
        ...


@runtime_checkable
class PluginManager(Protocol):
    """Minimal plugin manager interface."""

    def list_plugins(self) -> list[str]:
        """Return the names of loaded plugins."""
        ...


@runtime_checkable
class Logger(Protocol):
    """Minimal structured logger interface."""

    def info(self, msg: str, **kwargs: object) -> None:
        """Log an info-level message."""
        ...

    def warning(self, msg: str, **kwargs: object) -> None:
        """Log a warning-level message."""
        ...

    def error(self, msg: str, **kwargs: object) -> None:
        """Log an error-level message."""
        ...


@runtime_checkable
class StorageProvider(Protocol):
    """Minimal storage provider interface."""

    def read(self, path: str) -> bytes:
        """Read raw bytes from *path*."""
        ...

    def write(self, path: str, data: bytes) -> None:
        """Write *data* to *path*."""
        ...

    def exists(self, path: str) -> bool:
        """Return True if *path* exists in storage."""
        ...

    def list_dir(self, path: str) -> list[str]:
        """Return entries under *path*."""
        ...


@runtime_checkable
class Configuration(Protocol):
    """Minimal workspace configuration interface."""

    def get(self, key: str, default: object = None) -> object:
        """Return the value for *key* or *default*."""
        ...

    def set(self, key: str, value: object) -> None:
        """Set *key* to *value*."""
        ...

    def keys(self) -> list[str]:
        """Return all configuration keys."""
        ...


@runtime_checkable
class Kernel(Protocol):
    """Minimal kernel interface for workspace-level operations."""
