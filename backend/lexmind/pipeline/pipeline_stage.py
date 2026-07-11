"""Pipeline stage declarations and interfaces.

Declares the canonical processing stages and the contract each stage must
implement. Stages are declarations only — no processing logic (OCR,
parsing, embeddings, indexing) is implemented here.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from lexmind.core.health import Health, HealthStatus
from lexmind.exceptions import NotImplementedYetError
from lexmind.pipeline.pipeline_retry import NO_RETRY, RetryPolicy

if TYPE_CHECKING:
    from lexmind.pipeline.pipeline_context import PipelineContext
    from lexmind.pipeline.pipeline_result import StageResult


class StageId(StrEnum):
    """Canonical identifiers for the processing stages."""

    DOCUMENT_VALIDATION = "document_validation"
    METADATA_EXTRACTION = "metadata_extraction"
    OCR = "ocr"
    LANGUAGE_DETECTION = "language_detection"
    DOCUMENT_CLASSIFICATION = "document_classification"
    PARSER = "parser"
    ENTITY_EXTRACTION = "entity_extraction"
    CHUNKING = "chunking"
    EMBEDDINGS = "embeddings"
    INDEXING = "indexing"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    TIMELINE = "timeline"
    CONTRADICTION_DETECTION = "contradiction_detection"
    SEARCH_REGISTRATION = "search_registration"
    COMPLETED = "completed"


# Canonical execution order of the pipeline stages.
PIPELINE_STAGE_ORDER: tuple[StageId, ...] = (
    StageId.DOCUMENT_VALIDATION,
    StageId.METADATA_EXTRACTION,
    StageId.OCR,
    StageId.LANGUAGE_DETECTION,
    StageId.DOCUMENT_CLASSIFICATION,
    StageId.PARSER,
    StageId.ENTITY_EXTRACTION,
    StageId.CHUNKING,
    StageId.EMBEDDINGS,
    StageId.INDEXING,
    StageId.KNOWLEDGE_GRAPH,
    StageId.TIMELINE,
    StageId.CONTRADICTION_DETECTION,
    StageId.SEARCH_REGISTRATION,
    StageId.COMPLETED,
)


class StageStatus(StrEnum):
    """Execution status of a stage within a run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


@runtime_checkable
class PipelineStage(Protocol):
    """Contract every pipeline stage must satisfy."""

    id: StageId
    name: str
    description: str
    version: str
    enabled: bool
    dependencies: tuple[StageId, ...]
    estimated_duration_seconds: float
    retry_policy: RetryPolicy
    timeout_seconds: float | None

    def health(self) -> Health:
        """Return the current health of the stage."""
        ...

    def validate(self, context: "PipelineContext") -> bool:
        """Return True if the stage may run for the given context."""
        ...

    def execute(self, context: "PipelineContext") -> "StageResult":
        """Perform the stage's work and return its result."""
        ...

    def rollback(self, context: "PipelineContext") -> None:
        """Undo side effects of a failed or reverted execution."""
        ...


@dataclass
class BaseStage:
    """Base implementation providing sensible defaults for stages.

    Concrete processing stages are implemented in later tasks. The default
    ``execute`` raises ``NotImplementedYetError`` so declared stages remain
    inert until their behavior is provided.
    """

    id: StageId
    name: str
    description: str = ""
    version: str = "0.1.0"
    enabled: bool = True
    dependencies: tuple[StageId, ...] = ()
    estimated_duration_seconds: float = 0.0
    retry_policy: RetryPolicy = NO_RETRY
    timeout_seconds: float | None = None
    _health: HealthStatus = field(default=HealthStatus.HEALTHY, repr=False)

    def health(self) -> Health:
        """Return the current health of the stage."""
        return Health(module=f"stage:{self.id}", status=self._health)

    def validate(self, context: "PipelineContext") -> bool:
        """Return True if the stage may run. Default: use ``enabled``."""
        return self.enabled

    def execute(self, context: "PipelineContext") -> "StageResult":
        """Not implemented for declared stages."""
        raise NotImplementedYetError(f"Stage '{self.id}'")

    def rollback(self, context: "PipelineContext") -> None:
        """Default rollback is a no-op."""
        return None
