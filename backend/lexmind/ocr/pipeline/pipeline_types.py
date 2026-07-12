"""OCR pipeline value objects.

The OCR pipeline runs an ordered, composable sequence of processing steps
over a single document page image.  These value objects describe the options,
the per-step result and the aggregated pipeline result.  They are engine
agnostic and carry only plain data.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PipelineStepResult:
    """Output of a single OCR pipeline step.

    Attributes:
        step_name: Name of the step that produced the result.
        data: Primary step output (often the processed payload).
        metadata: Arbitrary, step-specific diagnostics.
        duration_ms: Wall-clock duration of the step in milliseconds.
    """

    step_name: str
    data: object
    metadata: dict[str, object] = field(default_factory=dict)
    duration_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class OcrPipelineOptions:
    """Declarative request controlling which pipeline steps run.

    Attributes:
        step_names: Ordered list of step names to execute.  A name is
            enabled (and therefore runs) when it appears in this list.
    """

    step_names: tuple[str, ...] = ()

    def enabled(self, name: str) -> bool:
        """Return True if *name* is part of the requested step sequence."""
        return name in self.step_names

    def keeps(self, step_name: str) -> bool:
        """Return True if *step_name* should run (alias of :meth:`enabled`)."""
        return self.enabled(step_name)


@dataclass(frozen=True, slots=True)
class OcrPipelineResult:
    """Outcome of an OCR pipeline run for one page.

    Attributes:
        page_number: Page identifier the pipeline ran against.
        step_results: Results of the steps that completed, in run order.
        final_text: Best-effort textual output assembled across steps.
        duration_ms: Total wall-clock duration of the run in milliseconds.
        is_success: True when every enabled step completed without error.
    """

    page_number: int
    step_results: tuple[PipelineStepResult, ...] = field(default_factory=tuple)
    final_text: str = ""
    duration_ms: float = 0.0
    is_success: bool = True

    @property
    def step_count(self) -> int:
        """Return the number of completed steps."""
        return len(self.step_results)
