"""Unit tests for domain events."""

from datetime import datetime

from lexmind.domain.events.base import DomainEvent
from lexmind.domain.events.domain_events import (
    AnnotationAdded,
    CitationAdded,
    DocumentImported,
    DocumentProcessed,
    EvidenceLinked,
    InvestigationCompleted,
    PersonIdentified,
    ReportGenerated,
    StatementCreated,
    TimelineUpdated,
)


class TestDomainEvent:
    def test_creation(self) -> None:
        e = DomainEvent(aggregate_id="a1")
        assert e.event_id
        assert isinstance(e.occurred_at, datetime)
        assert e.aggregate_id == "a1"

    def test_immutable(self) -> None:
        e = DomainEvent(aggregate_id="a1")
        try:
            e.event_id = "new"  # type: ignore[misc]
        except AttributeError:
            pass
        else:
            raise AssertionError("DomainEvent should be frozen")


class TestDocumentImported:
    def test_creation(self) -> None:
        e = DocumentImported(
            aggregate_id="d1",
            workspace_id="w1",
            file_path="docs/file.pdf",
            file_hash="abc123",
        )
        assert e.workspace_id == "w1"
        assert e.file_path == "docs/file.pdf"


class TestDocumentProcessed:
    def test_creation(self) -> None:
        e = DocumentProcessed(
            aggregate_id="d1",
            workspace_id="w1",
            processing_stages_completed=5,
        )
        assert e.processing_stages_completed == 5


class TestEvidenceLinked:
    def test_creation(self) -> None:
        e = EvidenceLinked(
            aggregate_id="e1",
            case_id="c1",
            evidence_id="e1",
        )
        assert e.case_id == "c1"


class TestStatementCreated:
    def test_creation(self) -> None:
        e = StatementCreated(
            aggregate_id="s1",
            case_id="c1",
            source_person_id="p1",
        )
        assert e.source_person_id == "p1"


class TestPersonIdentified:
    def test_creation(self) -> None:
        e = PersonIdentified(
            aggregate_id="p1",
            case_id="c1",
            person_name="John Doe",
        )
        assert e.person_name == "John Doe"


class TestTimelineUpdated:
    def test_creation(self) -> None:
        e = TimelineUpdated(
            aggregate_id="t1",
            case_id="c1",
            event_count=10,
        )
        assert e.event_count == 10


class TestCitationAdded:
    def test_creation(self) -> None:
        e = CitationAdded(
            aggregate_id="cr1",
            document_id="d1",
            citation_text="Art. 286",
        )
        assert e.citation_text == "Art. 286"


class TestAnnotationAdded:
    def test_creation(self) -> None:
        e = AnnotationAdded(
            aggregate_id="a1",
            document_id="d1",
            author_id="u1",
        )
        assert e.author_id == "u1"


class TestReportGenerated:
    def test_creation(self) -> None:
        e = ReportGenerated(
            aggregate_id="r1",
            case_id="c1",
            report_title="Summary",
        )
        assert e.report_title == "Summary"


class TestInvestigationCompleted:
    def test_creation(self) -> None:
        e = InvestigationCompleted(
            aggregate_id="i1",
            case_id="c1",
            finding_count=3,
        )
        assert e.finding_count == 3
