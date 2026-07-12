"""File watcher domain events."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from lexmind.domain.events.base import DomainEvent


class FileEventType(StrEnum):
    """Kind of change detected on a watched file."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True)
class FileEvent(DomainEvent):
    """Domain event emitted when a watched file changes.

    Instances are produced by the ``FileWatcher`` after filtering and
    debouncing raw backend notifications, then handed to an
    ``EventDispatcher`` (which normally forwards them to the EventBus).
    """

    workspace_id: str = ""
    watch_id: str = ""
    uri: str = ""
    name: str = ""
    event_type: FileEventType = FileEventType.CREATED
    size: int = 0
