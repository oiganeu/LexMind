"""Domain aggregates."""

from lexmind.domain.aggregates.case import CaseAggregate
from lexmind.domain.aggregates.document import DocumentAggregate
from lexmind.domain.aggregates.evidence_collection import EvidenceCollection
from lexmind.domain.aggregates.investigation import InvestigationAggregate
from lexmind.domain.aggregates.knowledge_graph import KnowledgeGraph
from lexmind.domain.aggregates.timeline import Timeline
from lexmind.domain.aggregates.workspace import WorkspaceAggregate

__all__ = [
    "CaseAggregate",
    "DocumentAggregate",
    "EvidenceCollection",
    "InvestigationAggregate",
    "KnowledgeGraph",
    "Timeline",
    "WorkspaceAggregate",
]
