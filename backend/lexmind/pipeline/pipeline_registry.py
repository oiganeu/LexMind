"""Pipeline stage registry with dependency validation."""

from lexmind.pipeline.pipeline_exceptions import (
    DuplicateStageError,
    StageDependencyError,
    StageNotFoundError,
)
from lexmind.pipeline.pipeline_stage import PipelineStage, StageId


class PipelineRegistry:
    """Holds registered stages and validates their dependency graph."""

    def __init__(self) -> None:
        self._stages: dict[StageId, PipelineStage] = {}

    def register(self, stage: PipelineStage) -> None:
        """Register a stage, rejecting duplicate ids."""
        if stage.id in self._stages:
            raise DuplicateStageError(f"Stage '{stage.id}' already registered")
        self._stages[stage.id] = stage

    def unregister(self, stage_id: StageId) -> None:
        """Remove a stage by id if present."""
        self._stages.pop(stage_id, None)

    def get(self, stage_id: StageId) -> PipelineStage:
        """Return a registered stage or raise ``StageNotFoundError``."""
        stage = self._stages.get(stage_id)
        if stage is None:
            raise StageNotFoundError(f"Stage '{stage_id}' is not registered")
        return stage

    def has(self, stage_id: StageId) -> bool:
        """Return True if a stage id is registered."""
        return stage_id in self._stages

    def all(self) -> list[PipelineStage]:
        """Return all registered stages."""
        return list(self._stages.values())

    def validate_dependencies(self) -> None:
        """Ensure all dependencies exist and the graph is acyclic."""
        self._check_missing()
        self._toposort()

    def topological_order(self) -> list[StageId]:
        """Return stage ids ordered so dependencies come first."""
        self._check_missing()
        return self._toposort()

    def _check_missing(self) -> None:
        for stage in self._stages.values():
            for dependency in stage.dependencies:
                if dependency not in self._stages:
                    raise StageDependencyError(
                        f"Stage '{stage.id}' depends on unregistered '{dependency}'"
                    )

    def _toposort(self) -> list[StageId]:
        ordered: list[StageId] = []
        visiting: set[StageId] = set()
        visited: set[StageId] = set()

        def visit(stage_id: StageId) -> None:
            if stage_id in visited:
                return
            if stage_id in visiting:
                raise StageDependencyError(f"Dependency cycle at '{stage_id}'")
            visiting.add(stage_id)
            for dependency in self._stages[stage_id].dependencies:
                visit(dependency)
            visiting.discard(stage_id)
            visited.add(stage_id)
            ordered.append(stage_id)

        for stage_id in self._stages:
            visit(stage_id)
        return ordered
