# Domain Layer

## Purpose

The Domain Layer contains the **core business model** of LexMind.
It defines the ubiquitous language, aggregates, entities, value objects,
domain events, repository interfaces, domain services, policies,
and specifications.

**Zero infrastructure dependencies.**

No ORM. No SQL. No FastAPI. No filesystem. No OCR. No AI.

Only pure business objects.

---

## DDD Principles

### Ubiquitous Language

Every class, method, and variable name in this layer uses the same
vocabulary that domain experts (lawyers, investigators, judges) use.

### Aggregates

An Aggregate is a cluster of domain objects treated as a single unit
for data changes.  Each Aggregate has a single **Aggregate Root** —
the only entry point for modifications.

| Aggregate | Root | Purpose |
|-----------|------|---------|
| `WorkspaceAggregate` | `Workspace` | Top-level container for documents and cases |
| `CaseAggregate` | `Case` | A legal case with linked evidence and documents |
| `DocumentAggregate` | `Document` | A document with version history |
| `EvidenceCollection` | (logical) | A set of evidence items for a case |
| `Timeline` | (logical) | Chronological events for a case |
| `KnowledgeGraph` | (logical) | Relationships between entities |
| `InvestigationAggregate` | `Investigation` | A structured inquiry with findings |

### Entities

Entities have **identity** — two entities with the same attributes
but different IDs are *not* equal.

Examples: `Workspace`, `Case`, `Document`, `Person`, `Evidence`.

### Value Objects

Value Objects are **immutable** and compared by **attribute equality**.

Examples: `Identifier`, `FileHash`, `FilePath`, `DateRange`,
`DocumentTitle`, `Language`, `Money`, `EmailAddress`.

### Domain Events

Domain Events capture something meaningful that happened:
`DocumentImported`, `EvidenceLinked`, `StatementCreated`, etc.

### Repository Interfaces

Repository interfaces define persistence contracts using `Protocol`.
Implementations live in the `infrastructure` layer.

### Domain Services

Services encapsulate logic that does not belong to a single entity:
`TimelineBuilder`, `DuplicateDetector`, `CitationResolver`, etc.

### Policies

Policies are stateless business rules:
`DuplicatePolicy`, `EvidencePolicy`, `RetentionPolicy`, etc.

### Specifications

Specifications are composable predicates:
`IsDuplicate`, `HasOCR`, `BelongsToWorkspace`, etc.

---

## Directory Structure

```
domain/
├── __init__.py              # Public API exports
├── README.md                # This file
├── aggregates/              # Aggregate roots
├── entities/                # Domain entities
├── value_objects/           # Immutable value objects
├── enums/                   # Domain enumerations
├── events/                  # Domain events
├── repositories/            # Repository interfaces (Protocol)
├── services/                # Domain service interfaces
├── policies/                # Business rule policies
├── specifications/          # Composable predicate specifications
├── factories/               # Entity/aggregate factory functions
└── exceptions/              # Domain-specific exceptions
```

---

## Invariants

- A document always belongs to one workspace.
- A document may belong to many cases.
- Evidence must reference at least one document.
- A statement must have a source (person or document).
- Timeline events require a date or time range.
- Annotations are immutable (append-only).
- Versions are append-only.
- Relationships cannot be self-referential.
