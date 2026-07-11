"""Unit tests for domain policies, specifications, and factories."""


from lexmind.domain.entities.document import Document
from lexmind.domain.entities.evidence import Evidence
from lexmind.domain.entities.workspace import Workspace
from lexmind.domain.enums.domain_enums import DocumentStatus
from lexmind.domain.factories.entity_factories import (
    create_annotation,
    create_case,
    create_document,
    create_document_aggregate,
    create_evidence,
    create_finding,
    create_investigation,
    create_person,
    create_statement,
    create_workspace,
)
from lexmind.domain.policies.domain_policies import (
    CitationPolicy,
    DuplicatePolicy,
    EvidencePolicy,
    RetentionPolicy,
    WorkspacePolicy,
)
from lexmind.domain.specifications.specifications import (
    BelongsToCase,
    BelongsToWorkspace,
    HasEmbeddings,
    HasOCR,
    IsDuplicate,
    IsProcessed,
)
from lexmind.domain.value_objects.file import FileHash


class TestDuplicatePolicy:
    def test_not_duplicate(self) -> None:
        p = DuplicatePolicy()
        doc = Document(workspace_id="w1", title="Test")
        assert not p.is_duplicate(doc, set())

    def test_marked_duplicate(self) -> None:
        p = DuplicatePolicy()
        doc = Document(workspace_id="w1", title="Test", is_duplicate=True)
        assert p.is_duplicate(doc, set())

    def test_hash_match(self) -> None:
        p = DuplicatePolicy()
        h = "a" * 40
        doc = Document(workspace_id="w1", title="Test", file_hash=FileHash(value=h))
        assert p.is_duplicate(doc, {h})


class TestEvidencePolicy:
    def test_valid(self) -> None:
        p = EvidencePolicy()
        ev = Evidence(document_ids=("d1",), case_ids=("c1",))
        assert p.is_valid(ev)

    def test_no_documents(self) -> None:
        p = EvidencePolicy()
        ev = Evidence(document_ids=("d1",), case_ids=())
        assert not p.is_valid(ev)


class TestCitationPolicy:
    def test_valid(self) -> None:
        p = CitationPolicy()
        assert p.is_valid("Art. 286", "d1")

    def test_empty_text(self) -> None:
        p = CitationPolicy()
        assert not p.is_valid("", "d1")


class TestRetentionPolicy:
    def test_can_delete(self) -> None:
        p = RetentionPolicy()
        doc = Document(workspace_id="w1", title="Test", status=DocumentStatus.DRAFT)
        assert p.can_delete(doc)

    def test_protected(self) -> None:
        p = RetentionPolicy()
        doc = Document(
            workspace_id="w1", title="Test", status=DocumentStatus.PROCESSING
        )
        assert not p.can_delete(doc)


class TestWorkspacePolicy:
    def test_can_add_document(self) -> None:
        p = WorkspacePolicy(max_documents=10)
        ws = Workspace(name="Test", owner_id="u1")
        assert p.can_add_document(ws)

    def test_limit_reached(self) -> None:
        p = WorkspacePolicy(max_documents=1)
        ws = Workspace(name="Test", owner_id="u1")
        ws.increment_document_count()
        assert not p.can_add_document(ws)

    def test_unlimited(self) -> None:
        p = WorkspacePolicy(max_documents=0)
        ws = Workspace(name="Test", owner_id="u1")
        for _ in range(100):
            ws.increment_document_count()
        assert p.can_add_document(ws)


class TestSpecifications:
    def test_is_duplicate(self) -> None:
        spec = IsDuplicate()
        doc = Document(workspace_id="w1", title="Test", is_duplicate=True)
        assert spec.is_satisfied_by(doc)

    def test_has_ocr(self) -> None:
        spec = HasOCR()
        doc = Document(workspace_id="w1", title="Test", has_ocr=True)
        assert spec.is_satisfied_by(doc)

    def test_is_processed(self) -> None:
        spec = IsProcessed()
        doc = Document(
            workspace_id="w1", title="Test", status=DocumentStatus.PROCESSED
        )
        assert spec.is_satisfied_by(doc)

    def test_has_embeddings(self) -> None:
        spec = HasEmbeddings()
        doc = Document(workspace_id="w1", title="Test", has_embeddings=True)
        assert spec.is_satisfied_by(doc)

    def test_belongs_to_workspace(self) -> None:
        spec = BelongsToWorkspace(workspace_id="w1")
        doc = Document(workspace_id="w1", title="Test")
        assert spec.is_satisfied_by(doc)
        doc2 = Document(workspace_id="w2", title="Other")
        assert not spec.is_satisfied_by(doc2)

    def test_belongs_to_case(self) -> None:
        spec = BelongsToCase(case_id="c1")
        ev = Evidence(document_ids=("d1",), case_ids=("c1",))
        assert spec.is_satisfied_by(ev)
        ev2 = Evidence(document_ids=("d1",), case_ids=("c2",))
        assert not spec.is_satisfied_by(ev2)

    def test_and_specification(self) -> None:
        spec = IsDuplicate() & HasOCR()
        doc = Document(
            workspace_id="w1", title="Test",
            is_duplicate=True, has_ocr=True,
        )
        assert spec.is_satisfied_by(doc)
        doc2 = Document(
            workspace_id="w1", title="Test",
            is_duplicate=True, has_ocr=False,
        )
        assert not spec.is_satisfied_by(doc2)

    def test_or_specification(self) -> None:
        spec = IsDuplicate() | HasOCR()
        doc = Document(
            workspace_id="w1", title="Test",
            is_duplicate=False, has_ocr=True,
        )
        assert spec.is_satisfied_by(doc)

    def test_not_specification(self) -> None:
        spec = ~IsDuplicate()
        doc = Document(workspace_id="w1", title="Test", is_duplicate=False)
        assert spec.is_satisfied_by(doc)
        doc2 = Document(workspace_id="w1", title="Test", is_duplicate=True)
        assert not spec.is_satisfied_by(doc2)

    def test_wrong_type_returns_false(self) -> None:
        spec = IsDuplicate()
        assert not spec.is_satisfied_by("not a document")


class TestFactories:
    def test_create_workspace(self) -> None:
        ws = create_workspace(name="Test", owner_id="u1")
        assert ws.name == "Test"

    def test_create_case(self) -> None:
        c = create_case(workspace_id="w1", title="Test Case")
        assert c.workspace_id == "w1"

    def test_create_document(self) -> None:
        d = create_document(workspace_id="w1", title="Test Doc")
        assert d.workspace_id == "w1"

    def test_create_document_aggregate(self) -> None:
        da = create_document_aggregate(workspace_id="w1", title="Test")
        assert da.document.workspace_id == "w1"

    def test_create_evidence(self) -> None:
        ev = create_evidence(document_ids=("d1",))
        assert "d1" in ev.document_ids

    def test_create_statement(self) -> None:
        s = create_statement(
            case_id="c1", content="Test", source_person_id="p1"
        )
        assert s.content == "Test"

    def test_create_person(self) -> None:
        p = create_person(first_name="John", last_name="Doe")
        assert p.full_name == "John Doe"

    def test_create_investigation(self) -> None:
        inv = create_investigation(case_id="c1", title="Audit")
        assert inv.case_id == "c1"

    def test_create_finding(self) -> None:
        f = create_finding(investigation_id="i1", title="Fraud")
        assert f.investigation_id == "i1"

    def test_create_annotation(self) -> None:
        a = create_annotation(
            document_id="d1", content="Note", author_id="u1"
        )
        assert a.content == "Note"
