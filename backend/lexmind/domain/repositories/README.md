# Repository Interfaces

## Purpose

This package defines the **persistence abstraction layer** for the LexMind domain model.

Repository interfaces isolate the domain from every storage technology.
Infrastructure implementations (PostgreSQL, SQLite, FAISS, etc.) will
live in ``backend/lexmind/infrastructure/``.

**No SQL. No ORM. No filesystem. Only contracts.**

---

## Repository Pattern

A Repository mediates between the domain and data mapping layers,
acting like an in-memory collection of domain objects.

Each aggregate root has its own repository interface that exposes
**business-oriented** query methods, not storage-oriented ones.

### BaseRepository

Every repository extends ``BaseRepository[T]`` which provides:

| Method | Description |
|--------|-------------|
| ``create(entity)`` | Persist a new entity |
| ``update(entity)`` | Persist changes to an existing entity |
| ``delete(entity_id)`` | Remove an entity by ID |
| ``get(entity_id)`` | Retrieve by ID |
| ``find(spec)`` | Find all matching a specification |
| ``find_one(spec)`` | Find first matching a specification |
| ``list_all()`` | Return all entities |
| ``list_page(page_request)`` | Paginated listing |
| ``count()`` | Total count |
| ``count_matching(spec)`` | Count matching a specification |
| ``exists(entity_id)`` | Check existence |

### Domain Repositories

| Repository | Entity | Key Queries |
|-----------|--------|-------------|
| ``WorkspaceRepository`` | Workspace | find_by_name, find_by_owner |
| ``CaseRepository`` | Case | find_by_workspace, find_by_status |
| ``DocumentRepository`` | Document | find_by_hash, find_by_status, find_duplicates |
| ``EvidenceRepository`` | Evidence | find_by_case, find_by_type |
| ``PersonRepository`` | Person | find_by_name, find_by_role |
| ``StatementRepository`` | Statement | find_by_person, find_by_type |
| ``TimelineRepository`` | TimelineEvent | find_by_date_range, list_ordered |
| ``CitationRepository`` | LegalCitation | find_by_document, find_by_law_reference |
| ``InvestigationRepository`` | Investigation | find_by_case, find_completed |
| ``OrganizationRepository`` | Organization | find_by_name, find_by_parent |
| ``AnnotationRepository`` | Annotation | find_by_document, find_by_page |
| ``GraphRepository`` | Relationship | find_connected, find_neighbors |
| ``ReportRepository`` | Report | find_by_case, find_by_format |
| ``SearchQueryRepository`` | SearchQuery | find_by_workspace |
| ``SearchResultRepository`` | SearchResult | find_by_query, find_top_results |

---

## Unit of Work

The ``UnitOfWork`` interface coordinates multiple repository operations
within a single transaction:

```
One application use case
    -> One Unit of Work
        -> One Commit
```

Methods: ``begin()``, ``commit()``, ``rollback()``, ``savepoint()``, ``release()``

---

## Pagination

``PageRequest`` and ``PageResult`` provide generic pagination:

- ``PageRequest``: page number, page size, sort fields, filters
- ``PageResult``: items, total count, has_next, has_previous, total_pages

Maximum page size: 100 items.

---

## Specifications

Repositories accept ``Specification`` objects for type-safe queries:

- ``DocumentsWithOCR`` — documents that have completed OCR
- ``DocumentsWithoutEmbeddings`` — documents pending embedding
- ``EvidenceByPerson`` — evidence linked to a person
- ``TimelineBetweenDates`` — events in a date range
- ``FindingsByRisk`` — findings at a risk level

Composed with ``&`` (AND), ``|`` (OR), ``~`` (NOT).

---

## Error Model

| Error | Description |
|-------|-------------|
| ``RepositoryError`` | Base repository error |
| ``ConcurrencyError`` | Optimistic lock conflict |
| ``EntityNotFoundError`` | Entity not found in store |
| ``DuplicateEntityError`` | Entity already exists |
| ``TransactionError`` | Transaction operation failed |

---

## Rules

- Repositories operate only on domain entities.
- Repositories never expose ORM models.
- Repositories never expose SQL.
- Repositories never expose filesystem paths.
- Repositories do not publish events (application services do).
