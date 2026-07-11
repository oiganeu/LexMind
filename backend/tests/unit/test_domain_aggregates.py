"""Unit tests for domain aggregates."""

import pytest

from lexmind.domain.aggregates.case import CaseAggregate
from lexmind.domain.aggregates.document import DocumentAggregate
from lexmind.domain.aggregates.evidence_collection import EvidenceCollection
from lexmind.domain.aggregates.investigation import InvestigationAggregate
from lexmind.domain.aggregates.knowledge_graph import KnowledgeGraph
from lexmind.domain.aggregates.timeline import Timeline
from lexmind.domain.aggregates.workspace import WorkspaceAggregate
from lexmind.domain.entities.case import Case
from lexmind.domain.entities.document import Document
from lexmind.domain.entities.evidence import Evidence
from lexmind.domain.entities.finding import Finding
from lexmind.domain.entities.relationship import Relationship
from lexmind.domain.entities.timeline_event import TimelineEvent
from lexmind.domain.entities.workspace import Workspace
from lexmind.domain.enums.domain_enums import EvidenceType, RelationshipType
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.file import FileHash, FilePath


class TestWorkspaceAggregate:
    def test_add_document(self) -> None:
        wa = WorkspaceAggregate(workspace=Workspace(name="Test", owner_id="u1"))
        wa.add_document("d1")
        assert wa.document_count == 1

    def test_add_duplicate_document_raises(self) -> None:
        wa = WorkspaceAggregate(workspace=Workspace(name="Test", owner_id="u1"))
        wa.add_document("d1")
        with pytest.raises(InvariantViolationError):
            wa.add_document("d1")

    def test_add_case(self) -> None:
        wa = WorkspaceAggregate(workspace=Workspace(name="Test", owner_id="u1"))
        wa.add_case("c1")
        assert wa.case_count == 1

    def test_add_collaborator(self) -> None:
        wa = WorkspaceAggregate(workspace=Workspace(name="Test", owner_id="u1"))
        wa.add_collaborator("u1")
        wa.add_collaborator("u1")  # duplicate noop
        assert len(wa._collaborator_ids) == 1

    def test_deactivate_activate(self) -> None:
        wa = WorkspaceAggregate(workspace=Workspace(name="Test", owner_id="u1"))
        wa.deactivate()
        assert not wa.workspace.is_active
        wa.activate()
        assert wa.workspace.is_active


class TestCaseAggregate:
    def test_add_document(self) -> None:
        ca = CaseAggregate(case=Case(workspace_id="w1", title="Test"))
        ca.add_document("d1")
        assert ca.document_count == 1

    def test_add_evidence(self) -> None:
        ca = CaseAggregate(case=Case(workspace_id="w1", title="Test"))
        ca.add_evidence("e1")
        assert ca.evidence_count == 1

    def test_add_statement(self) -> None:
        ca = CaseAggregate(case=Case(workspace_id="w1", title="Test"))
        ca.add_statement("s1")
        assert "s1" in ca._statement_ids

    def test_close_with_documents(self) -> None:
        ca = CaseAggregate(case=Case(workspace_id="w1", title="Test"))
        ca.add_document("d1")
        ca.close()
        assert ca.status.value == "closed"

    def test_close_without_documents_raises(self) -> None:
        ca = CaseAggregate(case=Case(workspace_id="w1", title="Test"))
        with pytest.raises(InvariantViolationError):
            ca.close()

    def test_reopen(self) -> None:
        ca = CaseAggregate(case=Case(workspace_id="w1", title="Test"))
        ca.add_document("d1")
        ca.close()
        ca.reopen()
        assert ca.status.value == "reopened"


class TestDocumentAggregate:
    def test_import(self) -> None:
        da = DocumentAggregate(document=Document(workspace_id="w1", title="Test"))
        da.import_document(
            file_path=FilePath(value="docs/test.pdf"),
            file_hash=FileHash(value="a" * 40),
            mime_type="application/pdf",
        )
        assert da.status.value == "imported"
        assert da.version_count == 1

    def test_import_already_imported_raises(self) -> None:
        da = DocumentAggregate(document=Document(workspace_id="w1", title="Test"))
        fp = FilePath(value="docs/test.pdf")
        fh = FileHash(value="a" * 40)
        da.import_document(file_path=fp, file_hash=fh, mime_type="application/pdf")
        with pytest.raises(InvariantViolationError):
            da.import_document(file_path=fp, file_hash=fh, mime_type="application/pdf")

    def test_add_version(self) -> None:
        da = DocumentAggregate(document=Document(workspace_id="w1", title="Test"))
        da.import_document(
            file_path=FilePath(value="docs/test.pdf"),
            file_hash=FileHash(value="a" * 40),
            mime_type="application/pdf",
        )
        v = da.add_version(
            file_path=FilePath(value="docs/test_v2.pdf"),
            file_hash=FileHash(value="b" * 40),
            comment="Updated",
        )
        assert v.version_number == 2
        assert da.version_count == 2

    def test_version_draft_raises(self) -> None:
        da = DocumentAggregate(document=Document(workspace_id="w1", title="Test"))
        with pytest.raises(InvariantViolationError):
            da.add_version(
                file_path=FilePath(value="x.pdf"),
                file_hash=FileHash(value="a" * 40),
            )

    def test_mark_duplicate(self) -> None:
        da = DocumentAggregate(document=Document(workspace_id="w1", title="Test"))
        da.mark_duplicate()
        assert da.document.is_duplicate

    def test_latest_version(self) -> None:
        da = DocumentAggregate(document=Document(workspace_id="w1", title="Test"))
        assert da.latest_version is None
        da.import_document(
            file_path=FilePath(value="a.pdf"),
            file_hash=FileHash(value="a" * 40),
            mime_type="application/pdf",
        )
        assert da.latest_version is not None
        assert da.latest_version.version_number == 1


class TestEvidenceCollection:
    def test_add(self) -> None:
        ec = EvidenceCollection(case_id="c1")
        ev = Evidence(document_ids=("d1",))
        ec.add(ev)
        assert ec.count == 1

    def test_add_duplicate_raises(self) -> None:
        ec = EvidenceCollection(case_id="c1")
        ev = Evidence(document_ids=("d1",))
        ec.add(ev)
        with pytest.raises(InvariantViolationError):
            ec.add(ev)

    def test_by_type(self) -> None:
        ec = EvidenceCollection(case_id="c1")
        ec.add(Evidence(document_ids=("d1",), evidence_type=EvidenceType.DOCUMENTARY))
        ec.add(Evidence(document_ids=("d2",), evidence_type=EvidenceType.DIGITAL))
        assert len(ec.by_type(EvidenceType.DOCUMENTARY)) == 1


class TestTimeline:
    def test_add_event(self) -> None:
        t = Timeline(case_id="c1")
        ev = TimelineEvent(title="Event 1", date="2025-01-15")
        t.add_event(ev)
        assert t.event_count == 1

    def test_add_duplicate_raises(self) -> None:
        t = Timeline(case_id="c1")
        ev = TimelineEvent(title="Event 1", date="2025-01-15")
        t.add_event(ev)
        with pytest.raises(InvariantViolationError):
            t.add_event(ev)

    def test_ordered_events(self) -> None:
        t = Timeline(case_id="c1")
        t.add_event(TimelineEvent(title="B", date="2025-03-01"))
        t.add_event(TimelineEvent(title="A", date="2025-01-01"))
        ordered = t.ordered_events()
        assert ordered[0].date == "2025-01-01"
        assert ordered[1].date == "2025-03-01"


class TestKnowledgeGraph:
    def test_add_relationship(self) -> None:
        kg = KnowledgeGraph(case_id="c1")
        r = Relationship(
            source_entity_id="a",
            target_entity_id="b",
            relationship_type=RelationshipType.EMPLOYMENT,
        )
        kg.add_relationship(r)
        assert kg.relationship_count == 1

    def test_add_duplicate_raises(self) -> None:
        kg = KnowledgeGraph(case_id="c1")
        r = Relationship(
            source_entity_id="a",
            target_entity_id="b",
            relationship_type=RelationshipType.EMPLOYMENT,
        )
        kg.add_relationship(r)
        with pytest.raises(InvariantViolationError):
            kg.add_relationship(r)

    def test_node_ids(self) -> None:
        kg = KnowledgeGraph(case_id="c1")
        kg.add_relationship(Relationship(
            source_entity_id="a", target_entity_id="b",
            relationship_type=RelationshipType.REFERENCE,
        ))
        kg.add_relationship(Relationship(
            source_entity_id="b", target_entity_id="c",
            relationship_type=RelationshipType.CITATION,
        ))
        assert set(kg.node_ids) == {"a", "b", "c"}

    def test_connected_entities(self) -> None:
        kg = KnowledgeGraph(case_id="c1")
        kg.add_relationship(Relationship(
            source_entity_id="a", target_entity_id="b",
            relationship_type=RelationshipType.REFERENCE,
        ))
        kg.add_relationship(Relationship(
            source_entity_id="a", target_entity_id="c",
            relationship_type=RelationshipType.CITATION,
        ))
        assert set(kg.connected_entities("a")) == {"b", "c"}


class TestInvestigationAggregate:
    def test_add_finding(self) -> None:
        ia = InvestigationAggregate(
            investigation=__import__(
                "lexmind.domain.entities.investigation", fromlist=["Investigation"]
            ).Investigation(case_id="c1", title="Audit")
        )
        f = Finding(investigation_id=ia.id, title="Fraud found")
        ia.add_finding(f)
        assert ia.finding_count == 1

    def test_complete_without_findings_raises(self) -> None:
        ia = InvestigationAggregate(
            investigation=__import__(
                "lexmind.domain.entities.investigation", fromlist=["Investigation"]
            ).Investigation(case_id="c1", title="Audit")
        )
        with pytest.raises(InvariantViolationError):
            ia.complete()

    def test_complete_with_findings(self) -> None:
        inv = __import__(
            "lexmind.domain.entities.investigation", fromlist=["Investigation"]
        ).Investigation(case_id="c1", title="Audit")
        ia = InvestigationAggregate(investigation=inv)
        f = Finding(investigation_id=ia.id, title="Fraud found")
        ia.add_finding(f)
        ia.complete()
        assert ia.is_completed
