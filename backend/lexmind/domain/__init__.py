"""LexMind Domain Layer.

Pure business objects with zero infrastructure dependencies.

This package contains:
    - **Aggregates**: Workspace, Case, Document, EvidenceCollection,
      Timeline, KnowledgeGraph, Investigation.
    - **Entities**: Workspace, Case, Document, DocumentVersion, Evidence,
      Statement, Witness, Person, Organization, Meeting, TimelineEvent,
      Annotation, LegalCitation, LawReference, CourtDecision,
      Investigation, Finding, Relationship, Tag, Folder, Bookmark,
      SearchQuery, SearchResult, Report.
    - **Value Objects**: Identifier, FileHash, FilePath, DateRange,
      DocumentTitle, Language, Coordinate, PageNumber, ConfidenceScore,
      Version, Citation, EmailAddress, PhoneNumber, Money, Address,
      GeoLocation, TagSet, WorkspaceId, CaseId, DocumentId, EvidenceId.
    - **Enumerations**: DocumentStatus, DocumentType, EvidenceType,
      PersonRole, RelationshipType, StatementType, MeetingType,
      ImportStatus, ProcessingStatus, CaseStatus, RiskLevel,
      ConfidenceLevel, Language, Country, CourtLevel.
    - **Domain Events**: DocumentImported, DocumentProcessed,
      EvidenceLinked, StatementCreated, PersonIdentified,
      TimelineUpdated, CitationAdded, AnnotationAdded,
      ReportGenerated, InvestigationCompleted.
    - **Repository Interfaces**: WorkspaceRepository, CaseRepository,
      DocumentRepository, EvidenceRepository, StatementRepository,
      TimelineRepository, PersonRepository, CitationRepository.
    - **Domain Services**: TimelineBuilder, RelationshipResolver,
      DuplicateDetector, EvidenceMatcher, CitationResolver,
      ConflictDetector, DocumentClassifier.
    - **Policies**: DuplicatePolicy, EvidencePolicy, TimelinePolicy,
      CitationPolicy, RetentionPolicy, WorkspacePolicy.
    - **Specifications**: IsDuplicate, HasOCR, IsProcessed,
      HasEmbeddings, HasTimeline, HasGraph, BelongsToWorkspace,
      BelongsToCase.
    - **Factories**: create_workspace, create_case, create_document, etc.
    - **Exceptions**: DomainError, EntityNotFoundError,
      InvariantViolationError, etc.

No ORM. No SQL. No FastAPI. No filesystem. Only business logic.
"""

from lexmind.domain import (
    aggregates,
    entities,
    enums,
    events,
    exceptions,
    factories,
    policies,
    repositories,
    services,
    specifications,
    value_objects,
)

__all__ = [
    "aggregates",
    "entities",
    "enums",
    "events",
    "exceptions",
    "factories",
    "policies",
    "repositories",
    "services",
    "specifications",
    "value_objects",
]
