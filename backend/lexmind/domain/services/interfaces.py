"""Domain service interfaces — pure contracts.

Services encapsulate domain logic that does not naturally
belong to a single entity or aggregate.  These are Protocol
definitions; implementations live in the application layer.
"""

from typing import Protocol, runtime_checkable

from lexmind.domain.entities.document import Document
from lexmind.domain.entities.evidence import Evidence
from lexmind.domain.entities.legal_citation import LegalCitation
from lexmind.domain.entities.person import Person
from lexmind.domain.entities.relationship import Relationship
from lexmind.domain.entities.statement import Statement
from lexmind.domain.entities.timeline_event import TimelineEvent


@runtime_checkable
class TimelineBuilder(Protocol):
    """Builds a chronological timeline from documents and statements."""

    def build_from_documents(
        self, documents: list[Document]
    ) -> list[TimelineEvent]: ...

    def build_from_statements(
        self, statements: list[Statement]
    ) -> list[TimelineEvent]: ...

    def merge_timelines(
        self, *timelines: list[TimelineEvent]
    ) -> list[TimelineEvent]: ...


@runtime_checkable
class RelationshipResolver(Protocol):
    """Discovers and resolves relationships between entities."""

    def resolve_between_documents(
        self, doc_a: Document, doc_b: Document
    ) -> Relationship | None: ...

    def resolve_from_statement(
        self, statement: Statement, persons: list[Person]
    ) -> list[Relationship]: ...


@runtime_checkable
class DuplicateDetector(Protocol):
    """Detects duplicate documents based on content similarity."""

    def is_duplicate(
        self, candidate: Document, existing: Document
    ) -> bool: ...

    def find_duplicates(
        self, candidate: Document, documents: list[Document]
    ) -> list[Document]: ...


@runtime_checkable
class EvidenceMatcher(Protocol):
    """Matches evidence to relevant cases and documents."""

    def match_to_case(
        self, evidence: Evidence, documents: list[Document]
    ) -> list[Document]: ...

    def score_relevance(
        self, evidence: Evidence, document: Document
    ) -> float: ...


@runtime_checkable
class CitationResolver(Protocol):
    """Resolves legal citations to their source laws."""

    def resolve(self, citation: LegalCitation) -> str | None: ...

    def validate_citation(self, citation_text: str) -> bool: ...


@runtime_checkable
class ConflictDetector(Protocol):
    """Detects contradictions between statements and documents."""

    def detect_conflicts(
        self, statements: list[Statement]
    ) -> list[tuple[Statement, Statement]]: ...

    def detect_document_conflicts(
        self, documents: list[Document]
    ) -> list[tuple[Document, Document]]: ...


@runtime_checkable
class DocumentClassifier(Protocol):
    """Classifies documents by type and content."""

    def classify(self, document: Document) -> str: ...

    def extract_entities(self, document: Document) -> list[str]: ...
