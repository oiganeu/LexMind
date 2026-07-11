"""Entity and aggregate factory functions.

Factories centralise complex creation logic and ensure that
entities are created in a valid state.
"""

from lexmind.domain.aggregates.document import DocumentAggregate
from lexmind.domain.entities.annotation import Annotation
from lexmind.domain.entities.case import Case
from lexmind.domain.entities.document import Document
from lexmind.domain.entities.evidence import Evidence
from lexmind.domain.entities.finding import Finding
from lexmind.domain.entities.investigation import Investigation
from lexmind.domain.entities.person import Person
from lexmind.domain.entities.statement import Statement
from lexmind.domain.entities.workspace import Workspace
from lexmind.domain.enums.domain_enums import (
    EvidenceType,
    PersonRole,
    StatementType,
)


def create_workspace(name: str, owner_id: str, description: str = "") -> Workspace:
    """Create a new workspace in a valid initial state."""
    return Workspace(name=name, owner_id=owner_id, description=description)


def create_case(workspace_id: str, title: str, description: str = "") -> Case:
    """Create a new case in OPEN status."""
    return Case(
        workspace_id=workspace_id, title=title, description=description
    )


def create_document(workspace_id: str, title: str) -> Document:
    """Create a new document in DRAFT status."""
    return Document(workspace_id=workspace_id, title=title)


def create_document_aggregate(
    workspace_id: str, title: str
) -> DocumentAggregate:
    """Create a document aggregate ready for import."""
    doc = Document(workspace_id=workspace_id, title=title)
    return DocumentAggregate(document=doc)


def create_evidence(
    document_ids: tuple[str, ...],
    evidence_type: EvidenceType = EvidenceType.DOCUMENTARY,
    description: str = "",
) -> Evidence:
    """Create evidence referencing at least one document."""
    return Evidence(
        document_ids=document_ids,
        evidence_type=evidence_type,
        description=description,
    )


def create_statement(
    case_id: str,
    content: str,
    source_person_id: str | None = None,
    source_document_id: str | None = None,
    statement_type: StatementType = StatementType.TESTIMONY,
) -> Statement:
    """Create a statement with a source."""
    return Statement(
        case_id=case_id,
        content=content,
        source_person_id=source_person_id,
        source_document_id=source_document_id,
        statement_type=statement_type,
    )


def create_person(
    first_name: str, last_name: str, role: PersonRole = PersonRole.THIRD_PARTY
) -> Person:
    """Create a person entity."""
    return Person(first_name=first_name, last_name=last_name, role=role)


def create_investigation(case_id: str, title: str) -> Investigation:
    """Create an investigation in an open state."""
    return Investigation(case_id=case_id, title=title)


def create_finding(
    investigation_id: str, title: str, description: str = ""
) -> Finding:
    """Create a finding linked to an investigation."""
    return Finding(
        investigation_id=investigation_id,
        title=title,
        description=description,
    )


def create_annotation(
    document_id: str, content: str, author_id: str
) -> Annotation:
    """Create an annotation on a document."""
    return Annotation(
        document_id=document_id, content=content, author_id=author_id
    )
