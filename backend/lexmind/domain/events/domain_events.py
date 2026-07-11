"""Concrete domain events for the LexMind platform."""

from dataclasses import dataclass

from lexmind.domain.events.base import DomainEvent


@dataclass(frozen=True, slots=True)
class DocumentImported(DomainEvent):
    """Raised when a document has been successfully imported."""

    workspace_id: str = ""
    file_path: str = ""
    file_hash: str = ""


@dataclass(frozen=True, slots=True)
class DocumentProcessed(DomainEvent):
    """Raised when a document has completed processing."""

    workspace_id: str = ""
    processing_stages_completed: int = 0


@dataclass(frozen=True, slots=True)
class EvidenceLinked(DomainEvent):
    """Raised when evidence is linked to a case."""

    case_id: str = ""
    evidence_id: str = ""


@dataclass(frozen=True, slots=True)
class StatementCreated(DomainEvent):
    """Raised when a new statement is recorded."""

    case_id: str = ""
    source_person_id: str | None = None
    source_document_id: str | None = None


@dataclass(frozen=True, slots=True)
class PersonIdentified(DomainEvent):
    """Raised when a person is identified in a document."""

    case_id: str = ""
    person_name: str = ""


@dataclass(frozen=True, slots=True)
class TimelineUpdated(DomainEvent):
    """Raised when the case timeline is updated."""

    case_id: str = ""
    event_count: int = 0


@dataclass(frozen=True, slots=True)
class CitationAdded(DomainEvent):
    """Raised when a legal citation is added to a document."""

    document_id: str = ""
    citation_text: str = ""


@dataclass(frozen=True, slots=True)
class AnnotationAdded(DomainEvent):
    """Raised when an annotation is created on a document."""

    document_id: str = ""
    author_id: str = ""


@dataclass(frozen=True, slots=True)
class ReportGenerated(DomainEvent):
    """Raised when a report is generated for a case."""

    case_id: str = ""
    report_title: str = ""


@dataclass(frozen=True, slots=True)
class InvestigationCompleted(DomainEvent):
    """Raised when an investigation reaches completion."""

    case_id: str = ""
    finding_count: int = 0
