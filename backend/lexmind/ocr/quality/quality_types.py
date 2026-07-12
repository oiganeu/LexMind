"""OCR quality value objects.

These types describe *what* an OCR quality assessment produces.  A
:class:`QualityMetric` is a single named, weighted score in ``[0, 1]``.
An :class:`OcrQualityReport` aggregates the metrics into an overall weighted
score and decides whether the OCR output is low quality.  :class:`OcrQualityOptions`
declares which calculators run and the low-quality threshold.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class QualityMetric:
    """A single named, weighted OCR quality score.

    Attributes:
        name: Unique metric/calculator name.
        score: Quality score in ``[0, 1]`` (1 = perfect).
        weight: Relative importance in ``[0, +inf)`` for aggregation.
        details: Free-form diagnostic information produced by the calculator.
    """

    name: str
    score: float
    weight: float = 1.0
    details: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0 and 1")
        if self.weight < 0.0:
            raise ValueError("weight must be non-negative")


@dataclass(frozen=True, slots=True)
class OcrQualityReport:
    """Aggregated outcome of an OCR quality assessment.

    Attributes:
        overall_score: Weighted average of the individual metric scores.
        metrics: The individual metrics that contributed to the score.
        warnings: Non-fatal notes (e.g. calculators that failed safely).
        threshold: Low-quality cutoff used by :attr:`is_low_quality`.
    """

    overall_score: float
    metrics: tuple[QualityMetric, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    threshold: float = 0.5

    @property
    def is_low_quality(self) -> bool:
        """Return True when the overall score falls below the threshold."""
        return self.overall_score < self.threshold

    @classmethod
    def build(
        cls,
        metrics: tuple[QualityMetric, ...],
        threshold: float = 0.5,
        warnings: tuple[str, ...] = (),
        overall_score: float | None = None,
    ) -> OcrQualityReport:
        """Construct a report, computing the weighted overall score.

        Args:
            metrics: Metrics to aggregate.
            threshold: Low-quality cutoff.
            warnings: Non-fatal notes.
            overall_score: Explicit overall score; when ``None`` it is computed
                as the weight-weighted average of *metrics* (0.0 if no weight).

        Returns:
            A populated :class:`OcrQualityReport`.
        """
        if overall_score is None:
            total_weight = sum(metric.weight for metric in metrics)
            if total_weight <= 0.0:
                overall_score = 0.0
            else:
                overall_score = (
                    sum(metric.score * metric.weight for metric in metrics)
                    / total_weight
                )
        return cls(
            overall_score=overall_score,
            metrics=tuple(metrics),
            warnings=tuple(warnings),
            threshold=threshold,
        )


@dataclass(frozen=True, slots=True)
class OcrQualityOptions:
    """Declarative request for an OCR quality assessment.

    Attributes:
        threshold: Overall score below which output is low quality.
        enabled_metrics: Restrict to these metric names.  Empty means "all".
    """

    threshold: float = 0.5
    enabled_metrics: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")

    def is_enabled(self, name: str) -> bool:
        """Return True if *name* should run (all when none are restricted)."""
        if not self.enabled_metrics:
            return True
        return name in self.enabled_metrics

    def keeps(self, score: float) -> bool:
        """Return True when *score* meets or exceeds the threshold."""
        return score >= self.threshold
