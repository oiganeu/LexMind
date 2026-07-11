# Ubiquitous Language

This document defines every business term used in the LexMind platform.
All developers, domain experts, and stakeholders share this vocabulary.

---

## Core Concepts

### Workspace
- **Definition**: The top-level organizational unit. All documents, cases, and collaborators belong to a workspace.
- **Examples**: "Civil Cases Workspace", "Corporate Investigations Workspace"
- **Rules**: A workspace must have a name and an owner. A workspace can be active or inactive.
- **Related**: Case, Document, Collaborator

### Case
- **Definition**: A legal matter under investigation or litigation. A case groups documents, evidence, persons, and analysis.
- **Examples**: "Smith v. Jones", "Tax Fraud Investigation 2026"
- **Rules**: A case belongs to exactly one workspace. A case may link to many documents. A case has a status (open, active, settled, closed).
- **Related**: Workspace, Document, Evidence, Person, Timeline

### Document
- **Definition**: A file or record imported into the platform for analysis. The central entity around which most processing revolves.
- **Examples**: "Contract signed 2025-01-15", "Police report #4521"
- **Rules**: A document belongs to one workspace. A document may appear in many cases. A document progresses through import and processing statuses. Documents have version history (append-only).
- **Related**: Workspace, Case, DocumentVersion, Evidence, Annotation

### Document Version
- **Definition**: An immutable snapshot of a document at a point in time. Versions are append-only.
- **Examples**: Version 1 (initial import), Version 2 (updated scan)
- **Rules**: Version numbers are sequential (>= 1). Versions cannot be modified after creation.
- **Related**: Document

### Evidence
- **Definition**: A piece of proof linked to one or more cases. Evidence must reference at least one document.
- **Examples**: "Photograph of accident scene", "Email correspondence"
- **Rules**: Evidence must reference at least one document. Evidence is classified by type (documentary, testimonial, digital, etc.).
- **Related**: Case, Document

### Statement
- **Definition**: A spoken or written assertion made in a legal context. Every statement must have a source.
- **Examples**: Witness testimony, deposition transcript, affidavit
- **Rules**: A statement must have a source (person or document). Statements are classified by type (testimony, deposition, affidavit, etc.).
- **Related**: Person, Document, Case, Witness

### Witness
- **Definition**: A person who provides testimony in a case. Wraps a Person with credibility assessment.
- **Examples**: "Expert witness Dr. Jane Smith"
- **Rules**: A witness is linked to a person and a case. Credibility can be assessed.
- **Related**: Person, Statement, Case

### Person
- **Definition**: A natural person involved in legal proceedings.
- **Examples**: "John Smith (defendant)", "Attorney Maria Garcia"
- **Rules**: A person has a role (client, attorney, witness, judge, etc.). A person may belong to many cases.
- **Related**: Case, Witness, Organization, Statement

### Organization
- **Definition**: A legal entity such as a company, agency, or court.
- **Examples**: "Acme Corp", "Bucharest District Court"
- **Rules**: An organization must have a name. An organization may have parent organizations.
- **Related**: Person, Case

### Meeting
- **Definition**: A recorded gathering relevant to a case.
- **Examples**: "Client intake meeting", "Mediation session"
- **Rules**: A meeting belongs to a case. A meeting has attendees and may produce statements.
- **Related**: Case, Person, Statement

---

## Legal Concepts

### Legal Citation
- **Definition**: A reference to a specific legal provision (article, paragraph, page).
- **Examples**: "Art. 286 Cod Penal", "Legea nr. 286/2009 art. 3 alin. (1)"
- **Rules**: Must have citation text. May reference a LawReference.
- **Related**: Document, LawReference

### Law Reference
- **Definition**: A specific law, regulation, or legal act.
- **Examples**: "Criminal Code (Legea 286/2009)", "EU Regulation 2016/679"
- **Rules**: Must have a title. May have an official number and year.
- **Related**: LegalCitation

### Court Decision
- **Definition**: A ruling or judgment issued by a court.
- **Examples**: "Sentinta civila nr. 123/2026"
- **Rules**: Must have a court name and decision date. Has a court level.
- **Related**: Case, CourtLevel

### Finding
- **Definition**: A conclusion reached during an investigation.
- **Examples**: "Financial irregularities detected", "No evidence of fraud"
- **Rules**: Must belong to an investigation. Has a confidence level.
- **Related**: Investigation, Document, Evidence

### Investigation
- **Definition**: A structured inquiry within a case, gathering evidence and reaching findings.
- **Examples**: "Financial audit investigation", "Witness credibility investigation"
- **Rules**: Must belong to a case. Must have findings before completion.
- **Related**: Case, Finding, Document, Evidence

---

## Technical Concepts

### Timeline Event
- **Definition**: A point or range on a chronological axis for a case.
- **Examples**: "2025-01-15: Contract signed", "2025-03-01 to 2025-03-15: Negotiation period"
- **Rules**: Must have a date or date range. Must have at least one source.
- **Related**: Case, Document, Statement

### Relationship
- **Definition**: A typed link between two entities in the knowledge graph.
- **Examples**: "Person A employed by Organization B", "Document C contradicts Document D"
- **Rules**: Source and target must be different entities. Has a type and optional weight.
- **Related**: KnowledgeGraph

### Annotation
- **Definition**: An immutable note attached to a document.
- **Examples**: "Key clause highlighted", "Contradiction with Exhibit B"
- **Rules**: Must reference a document. Must have content. Is immutable (append-only).
- **Related**: Document

### Tag
- **Definition**: A user-defined label for organizing entities.
- **Examples**: "urgent", "confidential", "expert-witness"
- **Rules**: Must have a name. Names are normalized to lowercase.
- **Related**: Document, Case, Evidence

### Folder
- **Definition**: A virtual container for organizing documents within a workspace.
- **Examples**: "Contracts", "Correspondence", "Expert Reports"
- **Rules**: Must belong to a workspace. May have a parent folder (tree structure).
- **Related**: Workspace, Document

### Bookmark
- **Definition**: A user-saved position within a document.
- **Examples**: "Page 5 of Contract — key termination clause"
- **Rules**: Must reference a document.
- **Related**: Document, User

### Search Query
- **Definition**: A user-initiated search within a workspace or case.
- **Examples**: "Find all emails mentioning 'breach of contract'"
- **Rules**: Must have query text. Scoped to a workspace, optionally a case.
- **Related**: Workspace, Case, SearchResult

### Search Result
- **Definition**: A single result returned by a search query.
- **Examples**: "Document X — score 0.95 — snippet: 'breach of contract terms...'"
- **Rules**: Must reference a query and a document. Has a relevance score.
- **Related**: SearchQuery, Document

### Report
- **Definition**: A generated analysis output for a case or investigation.
- **Examples**: "Case Summary Report", "Evidence Matrix"
- **Rules**: Must belong to a case. Must have a title.
- **Related**: Case, Investigation, Document

### Chunk
- **Definition**: A segment of a document created during the chunking processing stage, used for embedding and retrieval.
- **Examples**: "Page 1-3 of Contract", "Paragraph about liability"
- **Rules**: Created during processing. Linked to the source document.
- **Related**: Document, Embedding

### Import Job
- **Definition**: A batch operation that discovers, validates, and imports files into the platform.
- **Examples**: "Import 50 PDFs from /cases/2026/"
- **Rules**: Has a status (pending, discovering, importing, completed, failed). Tracks progress.
- **Related**: Document, Workspace

### Retrieval Result
- **Definition**: A result from semantic search over embedded document chunks.
- **Examples**: "Chunk from Contract page 5 — similarity 0.92"
- **Rules**: Has a similarity score. References a document chunk.
- **Related**: Chunk, SearchQuery

### AI Answer
- **Definition**: A response generated by an AI model based on retrieved context.
- **Examples**: "Based on the contracts, the termination clause allows..."
- **Rules**: Generated from retrieval results. Includes confidence score. May include citations.
- **Related**: Retrieval Result, Citation

---

## Status Enumerations

### Document Status
`DRAFT → PENDING_IMPORT → IMPORTING → IMPORTED → PROCESSING → PROCESSED | FAILED → ARCHIVED | DELETED`

### Processing Status
`PENDING → VALIDATING → EXTRACTING_METADATA → OCR → LANGUAGE_DETECTION → CLASSIFYING → PARSING → ENTITY_EXTRACTION → CHUNKING → EMBEDDING → INDEXING → KNOWLEDGE_GRAPH → TIMELINE → CONTRADICTION_CHECK → SEARCH_REGISTRATION → COMPLETED | FAILED`

### Case Status
`OPEN → ACTIVE → PENDING_REVIEW → SETTLED | CLOSED | ARCHIVED | REOPENED`

### Import Status
`PENDING → DISCOVERING → VALIDATING → IMPORTING → COMPLETED | FAILED | CANCELLED`
