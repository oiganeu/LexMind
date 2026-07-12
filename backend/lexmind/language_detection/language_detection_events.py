"""Domain events for language detection."""

from __future__ import annotations

from dataclasses import dataclass

from lexmind.events.event import Event


@dataclass(slots=True)
class LanguageDetectionStarted(Event):  # pragma: no cover - trivial
    """Emitted when a language detection run begins."""

    name: str = "language_detection_started"
    source_module: str = "language_detection"


@dataclass(slots=True)
class LanguageDetectionCompleted(Event):  # pragma: no cover - trivial
    """Emitted when a language detection run completes."""

    name: str = "language_detection_completed"
    source_module: str = "language_detection"
    language_count: int = 0
    detector: str = ""


@dataclass(slots=True)
class LanguageDetectionFailed(Event):  # pragma: no cover - trivial
    """Emitted when a language detection run fails."""

    name: str = "language_detection_failed"
    source_module: str = "language_detection"
    error_message: str = ""
