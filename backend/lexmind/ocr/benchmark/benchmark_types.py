"""OCR benchmark value objects.

The benchmark framework measures how well an OCR engine reproduces a set of
known reference texts.  A :class:`BenchmarkDataset` holds labelled
:class:`BenchmarkCase` samples; running an engine over the dataset yields a
:class:`BenchmarkResult` per case and an aggregate :class:`BenchmarkReport`.
All objects are engine-agnostic and carry only the data needed to score and
report accuracy/latency.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    """A single benchmark sample: an image and its expected text."""

    id: str
    expected_text: str
    image_ref: str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("case id must not be empty")


@dataclass(frozen=True, slots=True)
class BenchmarkDataset:
    """A named collection of benchmark cases."""

    name: str
    cases: tuple[BenchmarkCase, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("dataset name must not be empty")

    @property
    def case_count(self) -> int:
        """Return the number of cases in the dataset."""
        return len(self.cases)


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Outcome of running one OCR engine over one benchmark case."""

    engine_name: str
    case_id: str
    accuracy: float
    latency_ms: float

    def __post_init__(self) -> None:
        if not self.engine_name:
            raise ValueError("engine_name must not be empty")
        if not self.case_id:
            raise ValueError("case_id must not be empty")
        if not 0.0 <= self.accuracy <= 1.0:
            raise ValueError("accuracy must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    """Aggregate result of benchmarking one engine over one dataset."""

    engine_name: str
    dataset_name: str
    results: tuple[BenchmarkResult, ...]

    def __post_init__(self) -> None:
        if not self.engine_name:
            raise ValueError("engine_name must not be empty")
        if not self.dataset_name:
            raise ValueError("dataset_name must not be empty")

    @property
    def mean_accuracy(self) -> float:
        """Return the mean accuracy across all results (0.0 when empty)."""
        if not self.results:
            return 0.0
        return sum(r.accuracy for r in self.results) / len(self.results)

    @property
    def mean_latency(self) -> float:
        """Return the mean latency across all results (0.0 when empty)."""
        if not self.results:
            return 0.0
        return sum(r.latency_ms for r in self.results) / len(self.results)

    def is_acceptable(self, threshold: float) -> bool:
        """Return True if mean accuracy meets *threshold* (0-1)."""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        return self.mean_accuracy >= threshold
