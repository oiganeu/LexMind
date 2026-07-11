"""Pipeline definition.

A ``Pipeline`` is an ordered selection of registered stages to run for a
document. It does not execute anything itself; execution is delegated to
``PipelineExecutor``.
"""

from lexmind.pipeline.pipeline_registry import PipelineRegistry
from lexmind.pipeline.pipeline_stage import (
    PIPELINE_STAGE_ORDER,
    PipelineStage,
    StageId,
)


class Pipeline:
    """An ordered set of stages resolved against a registry."""

    def __init__(
        self,
        name: str,
        registry: PipelineRegistry,
        stage_order: tuple[StageId, ...] | None = None,
    ) -> None:
        self.name = name
        self._registry = registry
        self._order = stage_order if stage_order is not None else PIPELINE_STAGE_ORDER

    @property
    def registry(self) -> PipelineRegistry:
        """Return the backing stage registry."""
        return self._registry

    @property
    def stage_order(self) -> tuple[StageId, ...]:
        """Return the configured stage order."""
        return self._order

    def stages(self) -> list[PipelineStage]:
        """Return registered stages in execution order.

        Stage ids in the order that are not registered are skipped so a
        partial pipeline can run against a subset of stages.
        """
        resolved: list[PipelineStage] = []
        for stage_id in self._order:
            if self._registry.has(stage_id):
                resolved.append(self._registry.get(stage_id))
        return resolved

    def validate(self) -> None:
        """Validate the dependency graph of the backing registry."""
        self._registry.validate_dependencies()
