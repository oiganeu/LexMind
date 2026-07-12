"""Domain events for image preprocessing."""

from __future__ import annotations

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class ImagePreprocessingStarted(DomainEvent):  # pragma: no cover - trivial
    """Emitted when a preprocessing run begins."""

    image_id: str = ""
    workspace_id: str = ""


@dataclass(frozen=True, slots=True)
class ImagePreprocessingCompleted(DomainEvent):  # pragma: no cover - trivial
    """Emitted when a preprocessing run finishes successfully."""

    image_id: str = ""
    workspace_id: str = ""
    applied_operations: tuple[str, ...] = ()
    output_size: int = 0


@dataclass(frozen=True, slots=True)
class ImagePreprocessingFailed(DomainEvent):  # pragma: no cover - trivial
    """Emitted when a preprocessing run fails."""

    image_id: str = ""
    workspace_id: str = ""
    error_message: str = ""
