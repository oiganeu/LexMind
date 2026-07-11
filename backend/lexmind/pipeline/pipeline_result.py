"""Stage and pipeline result models."""

from dataclasses import dataclass, field
from typing import Any

from lexmind.pipeline.pipeline_stage import StageId, StageStatus


@dataclass
class StageResult:
    """The outcome of executing a single stage."""

    stage_id: StageId
    status: StageStatus
    success: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    execution_time_seconds: float = 0.0
    output_metadata: dict[str, Any] = field(default_factory=dict)
    attempts: int = 1

    @classmethod
    def ok(cls, stage_id: StageId, **kwargs: Any) -> "StageResult":
        """Build a successful, completed result."""
        return cls(stage_id=stage_id, status=StageStatus.COMPLETED, success=True, **kwargs)

    @classmethod
    def failed(cls, stage_id: StageId, error: str, **kwargs: Any) -> "StageResult":
        """Build a failed result carrying an error message."""
        return cls(
            stage_id=stage_id,
            status=StageStatus.FAILED,
            success=False,
            errors=[error],
            **kwargs,
        )

    @classmethod
    def skipped(cls, stage_id: StageId, reason: str | None = None) -> "StageResult":
        """Build a skipped result."""
        warnings = [reason] if reason else []
        return cls(
            stage_id=stage_id,
            status=StageStatus.SKIPPED,
            success=True,
            warnings=warnings,
        )


@dataclass
class PipelineResult:
    """Aggregate result of a full pipeline run."""

    pipeline_id: str
    document_id: str
    stage_results: list[StageResult] = field(default_factory=list)
    completed: bool = False

    def add(self, result: StageResult) -> None:
        """Append a stage result."""
        self.stage_results.append(result)

    @property
    def succeeded(self) -> bool:
        """Return True if every executed stage succeeded."""
        return all(result.success for result in self.stage_results)

    def result_for(self, stage_id: StageId) -> StageResult | None:
        """Return the result for a stage id, if present."""
        for result in self.stage_results:
            if result.stage_id == stage_id:
                return result
        return None
