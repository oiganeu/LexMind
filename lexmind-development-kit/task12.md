# TASK-0012

## Title

Design the Core Domain Model (DDD)

---

## Goal

Design the business domain model for LexMind.

This task defines the language of the platform.

No infrastructure.

No FastAPI.

No SQL.

No OCR.

No AI.

No filesystem.

Only pure business objects.

The Domain Layer must have zero dependencies
on infrastructure frameworks.

---

# Objective

Create a rich Domain-Driven Design model that represents legal
documents, evidence and investigations.

The model must support future civil,
criminal,
administrative,
commercial
and European law plugins.

---

# Directory Structure

backend/lexmind/domain/

    README.md

    __init__.py

    aggregates/

    entities/

    value_objects/

    events/

    repositories/

    services/

    policies/

    specifications/

    factories/

    exceptions/

---

# Ubiquitous Language

Create

docs/03-domain/ubiquitous-language.md

Document every business term.

Examples

Workspace

Case

Evidence

Statement

Witness

Document

Attachment

Meeting

Decision

Article

Law

Citation

Timeline Event

Finding

Relationship

Annotation

Chunk

Import Job

Retrieval Result

AI Answer

Every term must have

Definition

Examples

Rules

Related concepts

---

# Aggregates

Define aggregate roots.

Workspace

Case

Document

Evidence Collection

Timeline

Knowledge Graph

Investigation

---

# Core Entities

Declare interfaces and domain models for

Workspace

Case

Document

DocumentVersion

Evidence

Statement

Witness

Person

Organization

Meeting

TimelineEvent

Annotation

LegalCitation

LawReference

CourtDecision

Investigation

Finding

Relationship

Tag

Folder

Bookmark

SearchQuery

SearchResult

Report

No persistence.

No ORM.

---

# Value Objects

Create

Identifier

FileHash

FilePath

DateRange

DocumentTitle

DocumentType

Language

Coordinate

PageNumber

ConfidenceScore

Version

Citation

EmailAddress

PhoneNumber

Money

Address

GeoLocation

TagSet

WorkspaceId

CaseId

DocumentId

EvidenceId

Every Value Object

must be immutable.

---

# Enumerations

Create

DocumentStatus

DocumentType

EvidenceType

PersonRole

RelationshipType

StatementType

MeetingType

ImportStatus

ProcessingStatus

CaseStatus

RiskLevel

ConfidenceLevel

Language

Country

CourtLevel

---

# Domain Events

Define

DocumentImported

DocumentProcessed

EvidenceLinked

StatementCreated

PersonIdentified

TimelineUpdated

CitationAdded

AnnotationAdded

ReportGenerated

InvestigationCompleted

No implementation.

---

# Repository Interfaces

Declare only interfaces.

WorkspaceRepository

CaseRepository

DocumentRepository

EvidenceRepository

StatementRepository

TimelineRepository

PersonRepository

CitationRepository

No SQL.

No SQLite.

No implementations.

---

# Domain Services

Declare interfaces.

TimelineBuilder

RelationshipResolver

DuplicateDetector

EvidenceMatcher

CitationResolver

ConflictDetector

DocumentClassifier

Only interfaces.

---

# Domain Policies

Declare

DuplicatePolicy

EvidencePolicy

TimelinePolicy

CitationPolicy

RetentionPolicy

WorkspacePolicy

---

# Specifications

Declare

IsDuplicate

HasOCR

IsProcessed

HasEmbeddings

HasTimeline

HasGraph

BelongsToWorkspace

BelongsToCase

---

# Domain Rules

Document all invariants.

Examples

A document always belongs to one workspace.

A document may belong to many cases.

Evidence must reference at least one document.

A statement must have a source.

Timeline events require a date or time range.

Annotations are immutable.

Versions are append-only.

---

# Documentation

Create

backend/lexmind/domain/README.md

Explain

DDD principles

Aggregates

Entities

Value Objects

Domain Events

Repositories

Services

Policies

Specifications

---

# Unit Tests

Verify

Value Objects are immutable.

Identifiers validate correctly.

Equality semantics.

Aggregate invariants.

Domain Events creation.

No infrastructure dependencies.

---

# Acceptance Criteria

Domain layer contains no infrastructure code.

No ORM annotations.

No framework imports.

No persistence logic.

Rich business model defined.

All interfaces documented.

---

# Estimated Time

8 hours

---

# Priority

Highest

---

# Dependencies

TASK-0011
