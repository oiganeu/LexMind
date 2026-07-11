"""Unit tests for domain entities."""

import pytest

from lexmind.domain.entities.annotation import Annotation
from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.entities.bookmark import Bookmark
from lexmind.domain.entities.case import Case
from lexmind.domain.entities.court_decision import CourtDecision
from lexmind.domain.entities.document import Document
from lexmind.domain.entities.document_version import DocumentVersion
from lexmind.domain.entities.evidence import Evidence
from lexmind.domain.entities.finding import Finding
from lexmind.domain.entities.folder import Folder
from lexmind.domain.entities.investigation import Investigation
from lexmind.domain.entities.law_reference import LawReference
from lexmind.domain.entities.legal_citation import LegalCitation
from lexmind.domain.entities.meeting import Meeting
from lexmind.domain.entities.organization import Organization
from lexmind.domain.entities.person import Person
from lexmind.domain.entities.relationship import Relationship
from lexmind.domain.entities.report import Report
from lexmind.domain.entities.search_query import SearchQuery
from lexmind.domain.entities.search_result import SearchResult
from lexmind.domain.entities.statement import Statement
from lexmind.domain.entities.tag import Tag
from lexmind.domain.entities.timeline_event import TimelineEvent
from lexmind.domain.entities.witness import Witness
from lexmind.domain.entities.workspace import Workspace
from lexmind.domain.enums.domain_enums import (
    CaseStatus,
    RelationshipType,
)
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


class TestBaseEntity:
    def test_id_generated(self) -> None:
        e = BaseEntity()
        assert e.id
        assert len(e.id) > 0

    def test_equality_by_id(self) -> None:
        e1 = BaseEntity(id="same")
        e2 = BaseEntity(id="same")
        assert e1 == e2

    def test_inequality(self) -> None:
        e1 = BaseEntity(id="a")
        e2 = BaseEntity(id="b")
        assert e1 != e2

    def test_hash_by_id(self) -> None:
        e1 = BaseEntity(id="same")
        e2 = BaseEntity(id="same")
        assert hash(e1) == hash(e2)

    def test_touch(self) -> None:
        e = BaseEntity()
        old = e.updated_at
        e.touch()
        assert e.updated_at >= old


class TestWorkspace:
    def test_valid_creation(self) -> None:
        w = Workspace(name="Test Workspace", owner_id="user-1")
        assert w.name == "Test Workspace"
        assert w.is_active

    def test_empty_name_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Workspace(name="")

    def test_deactivate_activate(self) -> None:
        w = Workspace(name="Test", owner_id="u1")
        w.deactivate()
        assert not w.is_active
        w.activate()
        assert w.is_active

    def test_increment_document_count(self) -> None:
        w = Workspace(name="Test", owner_id="u1")
        w.increment_document_count()
        assert w.document_count == 1


class TestCase:
    def test_valid_creation(self) -> None:
        c = Case(workspace_id="w1", title="Test Case")
        assert c.title == "Test Case"
        assert c.status == CaseStatus.OPEN

    def test_empty_title_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Case(workspace_id="w1", title="")

    def test_no_workspace_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Case(workspace_id="", title="Test")

    def test_add_document(self) -> None:
        c = Case(workspace_id="w1", title="Test")
        c.add_document("d1")
        assert "d1" in c.document_ids

    def test_add_duplicate_document_noop(self) -> None:
        c = Case(workspace_id="w1", title="Test")
        c.add_document("d1")
        c.add_document("d1")
        assert len(c.document_ids) == 1

    def test_close(self) -> None:
        c = Case(workspace_id="w1", title="Test")
        c.add_document("d1")
        c.close()
        assert c.status == CaseStatus.CLOSED

    def test_reopen(self) -> None:
        c = Case(workspace_id="w1", title="Test")
        c.close()
        c.reopen()
        assert c.status == CaseStatus.REOPENED

    def test_is_active(self) -> None:
        c = Case(workspace_id="w1", title="Test")
        assert c.is_active
        c.close()
        assert not c.is_active


class TestDocument:
    def test_valid_creation(self) -> None:
        d = Document(workspace_id="w1", title="Test Doc")
        assert d.workspace_id == "w1"

    def test_no_workspace_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Document(workspace_id="", title="Test")

    def test_link_to_case(self) -> None:
        d = Document(workspace_id="w1", title="Test")
        d.link_to_case("c1")
        assert "c1" in d.case_ids

    def test_status_transitions(self) -> None:
        d = Document(workspace_id="w1", title="Test")
        d.mark_imported()
        assert d.status.value == "imported"
        d.mark_processing()
        assert d.status.value == "processing"
        d.mark_processed()
        assert d.status.value == "processed"

    def test_add_tag(self) -> None:
        d = Document(workspace_id="w1", title="Test")
        d.add_tag("urgent")
        assert "urgent" in d.tag_names

    def test_increment_version(self) -> None:
        d = Document(workspace_id="w1", title="Test")
        v = d.increment_version()
        assert v == 1
        assert d.version_count == 1


class TestDocumentVersion:
    def test_valid(self) -> None:
        dv = DocumentVersion(document_id="d1", version_number=1)
        assert dv.document_id == "d1"

    def test_no_document_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            DocumentVersion(document_id="", version_number=1)

    def test_invalid_version_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            DocumentVersion(document_id="d1", version_number=0)


class TestEvidence:
    def test_valid(self) -> None:
        e = Evidence(document_ids=("d1",))
        assert len(e.document_ids) == 1

    def test_no_documents_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Evidence(document_ids=())

    def test_link_to_case(self) -> None:
        e = Evidence(document_ids=("d1",))
        e.link_to_case("c1")
        assert "c1" in e.case_ids


class TestStatement:
    def test_person_source(self) -> None:
        s = Statement(source_person_id="p1", case_id="c1", content="Test")
        assert s.has_person_source
        assert not s.has_document_source

    def test_document_source(self) -> None:
        s = Statement(source_document_id="d1", case_id="c1", content="Test")
        assert s.has_document_source

    def test_no_source_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Statement(case_id="c1", content="Test")


class TestPerson:
    def test_full_name(self) -> None:
        p = Person(first_name="John", last_name="Doe")
        assert p.full_name == "John Doe"


class TestOrganization:
    def test_valid(self) -> None:
        o = Organization(name="Acme Corp")
        assert o.name == "Acme Corp"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Organization(name="")


class TestMeeting:
    def test_valid(self) -> None:
        m = Meeting(case_id="c1", title="Strategy Meeting")
        assert m.case_id == "c1"

    def test_no_case_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Meeting(case_id="", title="Test")


class TestTimelineEvent:
    def test_with_date(self) -> None:
        e = TimelineEvent(title="Event", date="2025-01-15")
        assert e.date == "2025-01-15"

    def test_with_range(self) -> None:
        e = TimelineEvent(title="Event", date_range_start="2025-01-01")
        assert e.date_range_start == "2025-01-01"

    def test_no_date_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            TimelineEvent(title="Event")


class TestAnnotation:
    def test_valid(self) -> None:
        a = Annotation(document_id="d1", content="Note", author_id="u1")
        assert a.content == "Note"

    def test_no_document_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Annotation(document_id="", content="Note", author_id="u1")

    def test_empty_content_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Annotation(document_id="d1", content="", author_id="u1")

    def test_lock(self) -> None:
        a = Annotation(document_id="d1", content="Note", author_id="u1")
        a.lock()
        assert a.is_locked


class TestLegalCitation:
    def test_valid(self) -> None:
        lc = LegalCitation(document_id="d1", citation_text="Art. 286 Cod Penal")
        assert lc.citation_text == "Art. 286 Cod Penal"

    def test_empty_text_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            LegalCitation(document_id="d1", citation_text="")


class TestLawReference:
    def test_valid(self) -> None:
        lr = LawReference(title="Criminal Code", official_number="286/2009")
        assert lr.title == "Criminal Code"

    def test_empty_title_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            LawReference(title="")


class TestCourtDecision:
    def test_valid(self) -> None:
        cd = CourtDecision(
            court_name="Bucharest Court", decision_date="2025-01-15"
        )
        assert cd.court_name == "Bucharest Court"

    def test_no_court_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            CourtDecision(court_name="", decision_date="2025-01-15")


class TestInvestigation:
    def test_valid(self) -> None:
        inv = Investigation(case_id="c1", title="Financial Audit")
        assert inv.case_id == "c1"

    def test_no_case_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Investigation(case_id="", title="Test")


class TestFinding:
    def test_valid(self) -> None:
        f = Finding(investigation_id="i1", title="Fraud detected")
        assert f.investigation_id == "i1"

    def test_no_investigation_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Finding(investigation_id="", title="Test")


class TestRelationship:
    def test_valid(self) -> None:
        r = Relationship(
            source_entity_id="a", target_entity_id="b",
            relationship_type=RelationshipType.EMPLOYMENT,
        )
        assert r.source_entity_id == "a"

    def test_self_reference_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Relationship(source_entity_id="a", target_entity_id="a")

    def test_no_source_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Relationship(source_entity_id="", target_entity_id="b")


class TestTag:
    def test_valid(self) -> None:
        t = Tag(name="urgent")
        assert t.normalized_name == "urgent"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Tag(name="")


class TestFolder:
    def test_valid(self) -> None:
        f = Folder(workspace_id="w1", name="Contracts")
        assert f.name == "Contracts"

    def test_add_document(self) -> None:
        f = Folder(workspace_id="w1", name="Contracts")
        f.add_document("d1")
        assert "d1" in f.document_ids


class TestBookmark:
    def test_valid(self) -> None:
        b = Bookmark(document_id="d1", user_id="u1")
        assert b.document_id == "d1"

    def test_no_document_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Bookmark(document_id="", user_id="u1")


class TestSearchQuery:
    def test_valid(self) -> None:
        sq = SearchQuery(workspace_id="w1", query_text="fraud")
        assert sq.query_text == "fraud"

    def test_empty_query_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            SearchQuery(workspace_id="w1", query_text="")


class TestSearchResult:
    def test_valid(self) -> None:
        sr = SearchResult(query_id="q1", document_id="d1", score=0.95)
        assert sr.score == 0.95

    def test_no_query_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            SearchResult(query_id="", document_id="d1")


class TestReport:
    def test_valid(self) -> None:
        r = Report(case_id="c1", title="Summary Report")
        assert r.title == "Summary Report"

    def test_no_case_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Report(case_id="", title="Test")

    def test_empty_title_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Report(case_id="c1", title="")


class TestWitness:
    def test_add_statement(self) -> None:
        w = Witness(person_id="p1", case_id="c1")
        w.add_statement("s1")
        assert "s1" in w.statement_ids

    def test_credibility(self) -> None:
        w = Witness(person_id="p1", case_id="c1")
        w.mark_credible()
        assert w.is_credible is True
        w.mark_incredible()
        assert w.is_credible is False
