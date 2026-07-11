"""Repository interfaces for the domain layer.

This package defines persistence contracts using ``Protocol`` classes.
No SQL, no ORM, no filesystem — only method signatures that
infrastructure implementations must satisfy.

Components:
    - **BaseRepository**: Generic CRUD + pagination + specification queries.
    - **Unit of Work**: Transaction coordination.
    - **Pagination**: PageRequest, PageResult, SortField, Filter.
    - **Errors**: RepositoryError, ConcurrencyError, TransactionError.
    - **Query Specifications**: DocumentsWithOCR, EvidenceByPerson, etc.
    - **Domain Repositories**: 14 repository interfaces for all aggregates.
"""

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
from lexmind.domain.repositories.report_repository import ReportRepository
from lexmind.domain.repositories.search_repository import (
    SearchQueryRepository,
    SearchResultRepository,
)
from lexmind.domain.repositories.statement_repository import StatementRepository
from lexmind.domain.repositories.timeline_repository import TimelineRepository
from lexmind.domain.repositories.unit_of_work import UnitOfWork
from lexmind.domain.repositories.workspace_repository import WorkspaceRepository

__all__ = [
    "AnnotationRepository",
    "BaseRepository",
    "CaseRepository",
    "CitationRepository",
    "ConcurrencyError",
    "DocumentRepository",
    "DuplicateEntityError",
    "EntityNotFoundError",
    "EvidenceRepository",
    "Filter",
    "GraphRepository",
    "InvestigationRepository",
    "OrganizationRepository",
    "PageRequest",
    "PageResult",
    "PersonRepository",
    "ReportRepository",
    "RepositoryError",
    "SearchQueryRepository",
    "SearchResultRepository",
    "SortDirection",
    "SortField",
    "StatementRepository",
    "TimelineRepository",
    "TransactionError",
    "UnitOfWork",
    "WorkspaceRepository",
]
