"""Domain service interfaces."""

from lexmind.domain.services.interfaces import (
    CitationResolver,
    ConflictDetector,
    DocumentClassifier,
    DuplicateDetector,
    EvidenceMatcher,
    RelationshipResolver,
    TimelineBuilder,
)

__all__ = [
    "CitationResolver",
    "ConflictDetector",
    "DocumentClassifier",
    "DuplicateDetector",
    "EvidenceMatcher",
    "RelationshipResolver",
    "TimelineBuilder",
]
