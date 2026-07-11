"""Domain policies — business rules that govern entity behaviour.

Policies are stateless rule objects evaluated against domain
entities.  They return ``True`` when the policy is satisfied.
"""

from dataclasses import dataclass

from lexmind.domain.entities.document import Document
from lexmind.domain.entities.evidence import Evidence
from lexmind.domain.entities.workspace import Workspace
from lexmind.domain.enums.domain_enums import DocumentStatus


@dataclass(frozen=True, slots=True)
class DuplicatePolicy:
    """Determines whether a document should be treated as a duplicate.

    A document is a duplicate if:
        * Its hash matches an existing document in the same workspace.
        * It is already marked as duplicate.
    """

    max_hash_matches: int = 1

    def is_duplicate(
        self, candidate: Document, existing_hashes: set[str]
    ) -> bool:
        """Return True if the candidate should be treated as a duplicate."""
        if candidate.is_duplicate:
            return True
        return bool(candidate.file_hash and candidate.file_hash.value in existing_hashes)


@dataclass(frozen=True, slots=True)
class EvidencePolicy:
    """Validates evidence rules.

    Rules:
        * Evidence must reference at least one document.
        * Evidence must be linked to at least one case.
    """

    min_documents: int = 1
    min_cases: int = 1

    def is_valid(self, evidence: Evidence) -> bool:
        """Return True if the evidence satisfies all rules."""
        return (
            len(evidence.document_ids) >= self.min_documents
            and len(evidence.case_ids) >= self.min_cases
        )


@dataclass(frozen=True, slots=True)
class TimelinePolicy:
    """Validates timeline event rules.

    Rules:
        * Events must have a date or date range.
        * Events must be linked to at least one source.
    """

    def is_valid_event(self, event: "TimelineEvent") -> bool:  # noqa: F821
        """Return True if the event satisfies timeline rules."""
        has_date = event.date is not None or event.date_range_start is not None
        has_source = bool(
            event.source_document_ids or event.source_statement_ids
        )
        return has_date and has_source


@dataclass(frozen=True, slots=True)
class CitationPolicy:
    """Validates citation rules.

    Rules:
        * Citation text must not be empty.
        * Citation must reference a document.
    """

    def is_valid(self, citation_text: str, document_id: str) -> bool:
        """Return True if the citation satisfies all rules."""
        return bool(citation_text.strip()) and bool(document_id)


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    """Determines whether a document can be deleted.

    Rules:
        * Documents in PROCESSING status cannot be deleted.
        * Documents linked to active cases cannot be deleted.
    """

    protected_statuses: frozenset[DocumentStatus] = frozenset(
        {DocumentStatus.PROCESSING, DocumentStatus.IMPORTING}
    )

    def can_delete(self, document: Document) -> bool:
        """Return True if the document can be safely deleted."""
        return document.status not in self.protected_statuses


@dataclass(frozen=True, slots=True)
class WorkspacePolicy:
    """Validates workspace rules.

    Rules:
        * Workspace name must not be empty.
        * Workspace must have an owner.
        * Maximum documents per workspace (0 = unlimited).
        * Maximum cases per workspace (0 = unlimited).
    """

    max_documents: int = 0
    max_cases: int = 0

    def can_add_document(self, workspace: Workspace) -> bool:
        """Return True if a new document can be added."""
        if self.max_documents == 0:
            return True
        return workspace.document_count < self.max_documents

    def can_add_case(self, workspace: Workspace) -> bool:
        """Return True if a new case can be added."""
        if self.max_cases == 0:
            return True
        return workspace.case_count < self.max_cases
