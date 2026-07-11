"""Pipeline execution context and cancellation token."""

from dataclasses import dataclass, field
from typing import Any

from lexmind.pipeline.pipeline_statistics import PipelineStatistics


class CancellationToken:
    """Cooperative cancellation signal shared with running stages."""

    def __init__(self) -> None:
        self._cancelled = False
        self._reason: str | None = None

    @property
    def is_cancelled(self) -> bool:
        """Return True if cancellation has been requested."""
        return self._cancelled

    @property
    def reason(self) -> str | None:
        """Return the cancellation reason, if any."""
        return self._reason

    def cancel(self, reason: str | None = None) -> None:
        """Request cancellation with an optional reason."""
        self._cancelled = True
        self._reason = reason


@dataclass
class PipelineContext:
    """Shared collaborators for a single pipeline run.

    Collaborators are injected explicitly; no global state is used. Typed as
    optional ``Any`` so the framework does not depend on concrete kernel,
    event bus, or plugin manager implementations at this layer.
    """

    workspace: Any
    document: Any
    pipeline_id: str
    document_id: str
    configuration: Any = None
    logger: Any = None
    kernel: Any = None
    event_bus: Any = None
    plugin_manager: Any = None
    statistics: PipelineStatistics = field(default_factory=PipelineStatistics)
    cancellation_token: CancellationToken = field(default_factory=CancellationToken)
    shared: dict[str, Any] = field(default_factory=dict)

    @property
    def is_cancelled(self) -> bool:
        """Return True if cancellation has been requested for this run."""
        return self.cancellation_token.is_cancelled
