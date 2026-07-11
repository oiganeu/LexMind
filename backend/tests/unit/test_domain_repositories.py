"""Unit tests for repository interfaces, pagination, UoW, errors, and specs.

These tests verify that:
- Repository interfaces compile and are Protocol-checkable.
- Pagination model works correctly.
- UnitOfWork interface is valid.
- Error hierarchy is correct.
- Query specifications work.
- No infrastructure dependencies are introduced.
"""

import pytest

from lexmind.domain.entities.document import Document
from lexmind.domain.entities.evidence import Evidence
from lexmind.domain.entities.finding import Finding
from lexmind.domain.entities.person import Person
from lexmind.domain.entities.timeline_event import TimelineEvent
from lexmind.domain.enums.domain_enums import EvidenceType, RiskLevel
from lexmind.domain.repositories.annotation_repository import AnnotationRepository
from lexmind.domain.repositories.base_repository import BaseRepository
from lexmind.domain.repositories.case_repository import CaseRepository
from lexmind.domain.repositories.citation_repository import CitationRepository
from lexmind.domain.repositories.document_repository import DocumentRepository
from lexmind.domain.repositories.errors import (
    ConcurrencyError,
    DuplicateEntityError,
    EntityNotFoundError,
    RepositoryError,
    TransactionError,
)
from lexmind.domain.repositories.evidence_repository import EvidenceRepository
from lexmind.domain.repositories.graph_repository import GraphRepository
from lexmind.domain.repositories.investigation_repository import InvestigationRepository
from lexmind.domain.repositories.organization_repository import OrganizationRepository
from lexmind.domain.repositories.pagination import (
    Filter,
    PageRequest,
    PageResult,
    SortDirection,
    SortField,
)
from lexmind.domain.repositories.person_repository import PersonRepository
from lexmind.domain.repositories.query_specifications import (
    DocumentsByLanguage,
    DocumentsWithOCR,
    DocumentsWithoutEmbeddings,
    EvidenceByType,
    FindingsByRisk,
    PersonsByRole,
    TimelineBetweenDates,
)
from lexmind.domain.repositories.report_repository import ReportRepository
from lexmind.domain.repositories.search_repository import (
    SearchQueryRepository,
    SearchResultRepository,
)
from lexmind.domain.repositories.statement_repository import StatementRepository
from lexmind.domain.repositories.timeline_repository import TimelineRepository
from lexmind.domain.repositories.unit_of_work import UnitOfWork
from lexmind.domain.repositories.workspace_repository import WorkspaceRepository
from lexmind.exceptions import LexMindError

# --- Repository interface compilation tests ---


class TestRepositoryInterfacesCompile:
    """Verify all repository interfaces can be imported and are Protocols."""

    def test_base_repository_is_protocol(self) -> None:
        assert hasattr(BaseRepository, "__protocol_attrs__")

    def test_workspace_repository(self) -> None:
        assert hasattr(WorkspaceRepository, "find_by_name")
        assert hasattr(WorkspaceRepository, "find_by_owner")

    def test_case_repository(self) -> None:
        assert hasattr(CaseRepository, "find_by_workspace")
        assert hasattr(CaseRepository, "find_by_status")

    def test_document_repository(self) -> None:
        assert hasattr(DocumentRepository, "find_by_hash")
        assert hasattr(DocumentRepository, "find_duplicates")

    def test_evidence_repository(self) -> None:
        assert hasattr(EvidenceRepository, "find_by_case")
        assert hasattr(EvidenceRepository, "find_by_type")

    def test_person_repository(self) -> None:
        assert hasattr(PersonRepository, "find_by_name")
        assert hasattr(PersonRepository, "find_by_role")

    def test_statement_repository(self) -> None:
        assert hasattr(StatementRepository, "find_by_person")
        assert hasattr(StatementRepository, "find_by_type")

    def test_timeline_repository(self) -> None:
        assert hasattr(TimelineRepository, "find_by_date_range")
        assert hasattr(TimelineRepository, "list_ordered")

    def test_citation_repository(self) -> None:
        assert hasattr(CitationRepository, "find_by_document")
        assert hasattr(CitationRepository, "find_by_law_reference")

    def test_investigation_repository(self) -> None:
        assert hasattr(InvestigationRepository, "find_by_case")
        assert hasattr(InvestigationRepository, "find_completed")

    def test_organization_repository(self) -> None:
        assert hasattr(OrganizationRepository, "find_by_name")
        assert hasattr(OrganizationRepository, "find_by_parent")

    def test_annotation_repository(self) -> None:
        assert hasattr(AnnotationRepository, "find_by_document")
        assert hasattr(AnnotationRepository, "find_by_page")

    def test_graph_repository(self) -> None:
        assert hasattr(GraphRepository, "find_connected")
        assert hasattr(GraphRepository, "find_neighbors")

    def test_report_repository(self) -> None:
        assert hasattr(ReportRepository, "find_by_case")
        assert hasattr(ReportRepository, "find_by_format")

    def test_search_query_repository(self) -> None:
        assert hasattr(SearchQueryRepository, "find_by_workspace")

    def test_search_result_repository(self) -> None:
        assert hasattr(SearchResultRepository, "find_by_query")
        assert hasattr(SearchResultRepository, "find_top_results")


# --- Pagination tests ---


class TestSortField:
    def test_defaults(self) -> None:
        sf = SortField(field_name="name")
        assert sf.direction == SortDirection.ASC

    def test_desc(self) -> None:
        sf = SortField(field_name="created_at", direction=SortDirection.DESC)
        assert sf.direction == SortDirection.DESC


class TestFilter:
    def test_eq_filter(self) -> None:
        f = Filter(field_name="status", operator="eq", value="active")
        assert f.field_name == "status"
        assert f.value == "active"


class TestPageRequest:
    def test_defaults(self) -> None:
        pr = PageRequest()
        assert pr.page == 1
        assert pr.page_size == 20
        assert pr.offset == 0
        assert pr.limit == 20

    def test_page_2(self) -> None:
        pr = PageRequest(page=2, page_size=10)
        assert pr.offset == 10
        assert pr.limit == 10

    def test_invalid_page(self) -> None:
        with pytest.raises(ValueError):
            PageRequest(page=0)

    def test_invalid_page_size_too_large(self) -> None:
        with pytest.raises(ValueError):
            PageRequest(page_size=101)

    def test_invalid_page_size_zero(self) -> None:
        with pytest.raises(ValueError):
            PageRequest(page_size=0)

    def test_max_page_size(self) -> None:
        pr = PageRequest(page_size=100)
        assert pr.page_size == 100


class TestPageResult:
    def test_empty(self) -> None:
        pr = PageResult[int]()
        assert pr.is_empty
        assert pr.total_pages == 0
        assert not pr.has_next
        assert not pr.has_previous

    def test_with_items(self) -> None:
        pr = PageResult(items=(1, 2, 3), total_count=10, page=1, page_size=3)
        assert not pr.is_empty
        assert pr.total_pages == 4
        assert pr.has_next
        assert not pr.has_previous

    def test_last_page(self) -> None:
        pr = PageResult(items=(10,), total_count=10, page=4, page_size=3)
        assert not pr.has_next
        assert pr.has_previous

    def test_middle_page(self) -> None:
        pr = PageResult(items=(4, 5, 6), total_count=10, page=2, page_size=3)
        assert pr.has_next
        assert pr.has_previous


# --- Error model tests ---


class TestRepositoryErrors:
    def test_repository_error_is_lexmind_error(self) -> None:
        err = RepositoryError("test")
        assert isinstance(err, LexMindError)

    def test_concurrency_error(self) -> None:
        err = ConcurrencyError("Document", "d1")
        assert "Concurrency conflict" in str(err)
        assert err.entity_type == "Document"
        assert err.entity_id == "d1"

    def test_entity_not_found_error(self) -> None:
        err = EntityNotFoundError("Case", "c1")
        assert "not found" in str(err)

    def test_duplicate_entity_error(self) -> None:
        err = DuplicateEntityError("Workspace", "w1")
        assert "already exists" in str(err)

    def test_transaction_error(self) -> None:
        err = TransactionError("commit", "disk full")
        assert "commit" in str(err)
        assert "disk full" in str(err)

    def test_transaction_error_no_reason(self) -> None:
        err = TransactionError("rollback")
        assert "rollback" in str(err)


# --- Unit of Work interface test ---


class TestUnitOfWorkInterface:
    def test_has_required_methods(self) -> None:
        assert hasattr(UnitOfWork, "begin")
        assert hasattr(UnitOfWork, "commit")
        assert hasattr(UnitOfWork, "rollback")
        assert hasattr(UnitOfWork, "savepoint")
        assert hasattr(UnitOfWork, "release")


# --- Query specification tests ---


class TestQuerySpecifications:
    def test_documents_with_ocr(self) -> None:
        spec = DocumentsWithOCR()
        doc = Document(workspace_id="w1", title="Test", has_ocr=True)
        assert spec.is_satisfied_by(doc)
        doc2 = Document(workspace_id="w1", title="Test", has_ocr=False)
        assert not spec.is_satisfied_by(doc2)

    def test_documents_without_embeddings(self) -> None:
        spec = DocumentsWithoutEmbeddings()
        doc = Document(workspace_id="w1", title="Test", has_embeddings=False)
        assert spec.is_satisfied_by(doc)
        doc2 = Document(workspace_id="w1", title="Test", has_embeddings=True)
        assert not spec.is_satisfied_by(doc2)

    def test_evidence_by_type(self) -> None:
        spec = EvidenceByType(evidence_type=EvidenceType.DIGITAL)
        ev = Evidence(document_ids=("d1",), evidence_type=EvidenceType.DIGITAL)
        assert spec.is_satisfied_by(ev)
        ev2 = Evidence(document_ids=("d1",), evidence_type=EvidenceType.DOCUMENTARY)
        assert not spec.is_satisfied_by(ev2)

    def test_timeline_between_dates(self) -> None:
        spec = TimelineBetweenDates(start_date="2025-01-01", end_date="2025-12-31")
        ev = TimelineEvent(title="Event", date="2025-06-15")
        assert spec.is_satisfied_by(ev)
        ev2 = TimelineEvent(title="Event", date="2026-01-01")
        assert not spec.is_satisfied_by(ev2)

    def test_timeline_between_dates_no_date(self) -> None:
        spec = TimelineBetweenDates(start_date="2025-01-01", end_date="2025-12-31")
        ev = TimelineEvent(title="Event", date_range_start="2025-01-01")
        assert not spec.is_satisfied_by(ev)

    def test_documents_by_language(self) -> None:
        from lexmind.domain.value_objects.language import Language

        spec = DocumentsByLanguage(language_code="ro")
        doc = Document(workspace_id="w1", title="Test", language=Language(value="ro"))
        assert spec.is_satisfied_by(doc)
        doc2 = Document(workspace_id="w1", title="Test", language=Language(value="en"))
        assert not spec.is_satisfied_by(doc2)

    def test_documents_by_language_no_language(self) -> None:
        spec = DocumentsByLanguage(language_code="ro")
        doc = Document(workspace_id="w1", title="Test")
        assert not spec.is_satisfied_by(doc)

    def test_persons_by_role(self) -> None:
        from lexmind.domain.enums.domain_enums import PersonRole

        spec = PersonsByRole(role=PersonRole.ATTORNEY)
        p = Person(first_name="John", last_name="Doe", role=PersonRole.ATTORNEY)
        assert spec.is_satisfied_by(p)
        p2 = Person(first_name="Jane", last_name="Smith", role=PersonRole.JUDGE)
        assert not spec.is_satisfied_by(p2)

    def test_wrong_type_returns_false(self) -> None:
        spec = DocumentsWithOCR()
        assert not spec.is_satisfied_by("not a document")
        assert not spec.is_satisfied_by(42)

    def test_findings_by_risk(self) -> None:
        spec = FindingsByRisk(min_risk=RiskLevel.MEDIUM)
        f = Finding(investigation_id="i1", title="Test")
        assert spec.is_satisfied_by(f)


# --- No infrastructure dependency tests ---


class TestNoInfrastructureDependencies:
    """Verify the repository layer has no infrastructure imports."""

    def test_no_sql_imports(self) -> None:
        """Repository files must not import SQL or ORM modules."""
        import inspect

        import lexmind.domain.repositories as repos

        source = inspect.getsource(repos)
        forbidden = ["sqlalchemy", "sqlite", "psycopg", "asyncpg", "aiosqlite"]
        for mod in forbidden:
            assert mod not in source.lower(), f"Found infrastructure import: {mod}"

    def test_all_repositories_are_protocols(self) -> None:
        """All repository interfaces must be Protocol classes."""
        repos = [
            WorkspaceRepository,
            CaseRepository,
            DocumentRepository,
            EvidenceRepository,
            PersonRepository,
            StatementRepository,
            TimelineRepository,
            CitationRepository,
            InvestigationRepository,
            OrganizationRepository,
            AnnotationRepository,
            GraphRepository,
            ReportRepository,
            SearchQueryRepository,
            SearchResultRepository,
        ]
        for repo in repos:
            assert hasattr(repo, "__protocol_attrs__"), f"{repo.__name__} is not a Protocol"
