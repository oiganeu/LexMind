"""Domain events for the OCR cache."""
from __future__ import annotations

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class OcrCacheHit(DomainEvent):  # pragma: no cover - trivial
    """Emitted on a successful cache hit."""
    aggregate_id: str = ""


@dataclass(frozen=True, slots=True)
class OcrCacheMiss(DomainEvent):  # pragma: no cover - trivial
    """Emitted when a cache lookup misses."""
    aggregate_id: str = ""


@dataclass(frozen=True, slots=True)
class OcrCacheStored(DomainEvent):  # pragma: no cover - trivial
    """Emitted when a result is stored in the cache."""
    aggregate_id: str = ""
