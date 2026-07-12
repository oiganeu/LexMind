"""OCR pipeline step contract, context, registry and built-in steps.

A :class:`OcrPipelineStep` is a single, composable unit of work executed over
a page image.  Steps communicate through a shared :class:`PipelineContext`
that carries the raw image bytes and a mutable ``state`` dictionary so later
steps can build on earlier ones.  The :class:`OcrPipelineStepRegistry` maps
step names to implementations; :class:`IdentityPipelineStep` is a dependency
free passthrough shipped with the framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from lexmind.ocr.pipeline.pipeline_types import PipelineStepResult


@dataclass(frozen=True, slots=True)
class PipelineContext:
    """Per-run shared state passed to every pipeline step.

    Attributes:
        image_data: Raw page image bytes.
        page_number: Page identifier for the current run.
        state: Mutable dictionary shared across steps in one run.
    """

    image_data: bytes
    page_number: int = 1
    state: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class OcrPipelineStep(Protocol):
    """A single composable step in the OCR pipeline."""

    @property
    def name(self) -> str:
        """Return the unique step name."""
        ...

    def process(self, context: PipelineContext) -> PipelineStepResult:
        """Process *context* and return the step result."""
        ...


class OcrPipelineStepNotFoundError(ValueError):
    """Raised when no step is registered for a requested name."""


class IdentityPipelineStep:
    """No-dependency passthrough step that records the input image.

    It stores the original image bytes in ``data`` and exposes a best-effort
    decoded text preview plus the byte count in ``metadata``.  It is useful as
    a default first step and as a baseline in tests.
    """

    @property
    def name(self) -> str:
        """Return the step name."""
        return "identity"

    def process(self, context: PipelineContext) -> PipelineStepResult:
        """Record the input image and a decoded text preview."""
        text = context.image_data.decode("utf-8", errors="replace")
        return PipelineStepResult(
            step_name=self.name,
            data=context.image_data,
            metadata={"bytes": len(context.image_data), "text": text},
        )


class OcrPipelineStepRegistry:
    """Registry mapping step names to :class:`OcrPipelineStep` instances."""

    def __init__(self) -> None:
        self._steps: dict[str, OcrPipelineStep] = {}

    def register(self, step: OcrPipelineStep) -> None:
        """Register *step* under its ``name``.

        Raises:
            ValueError: If the step name is empty.
        """
        if not step.name:
            raise ValueError("step name must not be empty")
        self._steps[step.name] = step

    def get(self, name: str) -> OcrPipelineStep:
        """Return the step registered under *name*.

        Raises:
            OcrPipelineStepNotFoundError: If no step is registered.
        """
        step = self._steps.get(name)
        if step is None:
            raise OcrPipelineStepNotFoundError(
                f"No OCR pipeline step registered under '{name}'"
            )
        return step

    def has(self, name: str) -> bool:
        """Return True if a step is registered under *name*."""
        return name in self._steps

    def registered_names(self) -> list[str]:
        """Return the registered step names, sorted."""
        return sorted(self._steps)
