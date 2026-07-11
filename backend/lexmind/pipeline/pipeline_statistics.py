"""Pipeline execution metrics."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from lexmind.pipeline.pipeline_stage import StageId


@dataclass
class StageMetrics:
    """Metrics captured for a single stage execution."""

    stage_id: StageId
    start_time: datetime | None = None
    end_time: datetime | None = None
    cpu_time_seconds: float = 0.0
    memory_bytes: int = 0
    retries: int = 0
    failures: int = 0

    @property
    def duration_seconds(self) -> float:
        """Wall-clock duration of the stage, or 0 if incomplete."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()


@dataclass
class PipelineStatistics:
    """Aggregate metrics for a full pipeline run."""

    start_time: datetime | None = None
    end_time: datetime | None = None
    files_processed: int = 0
    skipped_stages: list[StageId] = field(default_factory=list)
    stage_metrics: dict[StageId, StageMetrics] = field(default_factory=dict)

    def start(self) -> None:
        """Mark the pipeline start time."""
        self.start_time = datetime.now(UTC)

    def finish(self) -> None:
        """Mark the pipeline end time."""
        self.end_time = datetime.now(UTC)

    def metrics_for(self, stage_id: StageId) -> StageMetrics:
        """Return (creating if needed) the metrics for a stage."""
        metrics = self.stage_metrics.get(stage_id)
        if metrics is None:
            metrics = StageMetrics(stage_id=stage_id)
            self.stage_metrics[stage_id] = metrics
        return metrics

    def mark_skipped(self, stage_id: StageId) -> None:
        """Record a skipped stage."""
        if stage_id not in self.skipped_stages:
            self.skipped_stages.append(stage_id)

    @property
    def total_retries(self) -> int:
        """Sum of retries across all stages."""
        return sum(m.retries for m in self.stage_metrics.values())

    @property
    def total_failures(self) -> int:
        """Sum of failures across all stages."""
        return sum(m.failures for m in self.stage_metrics.values())

    @property
    def duration_seconds(self) -> float:
        """Total wall-clock duration of the run, or 0 if incomplete."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()
