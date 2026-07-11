"""Domain entities - identity-based objects with lifecycle."""

from lexmind.domain.entities.annotation import Annotation
from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.entities.bookmark import Bookmark
from lexmind.domain.entities.case import Case
from lexmind.domain.entities.court_decision import CourtDecision
from lexmind.domain.entities.document import Document
from lexmind.domain.entities.document_version import DocumentVersion
from lexmind.domain.entities.evidence import Evidence
from lexmind.domain.entities.finding import Finding
from lexmind.domain.entities.folder import Folder
from lexmind.domain.entities.investigation import Investigation
from lexmind.domain.entities.law_reference import LawReference
from lexmind.domain.entities.legal_citation import LegalCitation
from lexmind.domain.entities.meeting import Meeting
from lexmind.domain.entities.organization import Organization
from lexmind.domain.entities.person import Person
from lexmind.domain.entities.relationship import Relationship
from lexmind.domain.entities.report import Report
from lexmind.domain.entities.search_query import SearchQuery
from lexmind.domain.entities.search_result import SearchResult
from lexmind.domain.entities.statement import Statement
from lexmind.domain.entities.tag import Tag
from lexmind.domain.entities.timeline_event import TimelineEvent
from lexmind.domain.entities.witness import Witness
from lexmind.domain.entities.workspace import Workspace

__all__ = [
    "Annotation",
    "BaseEntity",
    "Bookmark",
    "Case",
    "CourtDecision",
    "Document",
    "DocumentVersion",
    "Evidence",
    "Finding",
    "Folder",
    "Investigation",
    "LawReference",
    "LegalCitation",
    "Meeting",
    "Organization",
    "Person",
    "Relationship",
    "Report",
    "SearchQuery",
    "SearchResult",
    "Statement",
    "Tag",
    "TimelineEvent",
    "Witness",
    "Workspace",
]
