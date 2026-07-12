"""OCR benchmark engines, runner contract and registry.

A :class:`OcrBenchmarkEngine` is any OCR engine that can turn an image
reference into recognised text.  A :class:`BenchmarkRunner` executes an engine
against a :class:`~lexmind.ocr.benchmark.benchmark_types.BenchmarkDataset` and
produces a :class:`BenchmarkReport`.  The dependency-free
:class:`DefaultBenchmarkRunner` scores with a simple character/word overlap.
Runners are discoverable through the :class:`BenchmarkRunnerRegistry`.
"""

from __future__ import annotations

import time
from typing import Protocol, runtime_checkable

from lexmind.ocr.benchmark.benchmark_types import (
    BenchmarkCase,
    BenchmarkDataset,
    BenchmarkReport,
    BenchmarkResult,
)


@runtime_checkable
class OcrBenchmarkEngine(Protocol):
    """An OCR engine that recognises text from an image reference."""

    @property
    def name(self) -> str:
        """Return the unique engine name."""
        ...

    def recognize(self, image_ref: str) -> str:
        """Return the recognised text for the image at *image_ref*."""
        ...


@runtime_checkable
class BenchmarkRunner(Protocol):
    """Executes an OCR engine against a benchmark dataset."""

    @property
    def name(self) -> str:
        """Return the unique runner name."""
        ...

    def run(
        self,
        dataset: BenchmarkDataset,
        engine: OcrBenchmarkEngine,
        options: dict | None = None,
    ) -> BenchmarkReport:
        """Run *engine* over *dataset* and return a report."""
        ...


class BenchmarkRunnerNotFoundError(ValueError):
    """Raised when no runner is registered for a name."""


def _char_overlap(expected: str, actual: str) -> float:
    """Return the character-level similarity in [0, 1]."""
    if not expected:
        return 1.0
    if not actual:
        return 0.0
    expected_set = set(expected)
    actual_set = set(actual)
    if not expected_set:
        return 1.0
    return len(expected_set & actual_set) / len(expected_set)


def _word_overlap(expected: str, actual: str) -> float:
    """Return the word-level similarity in [0, 1]."""
    if not expected:
        return 1.0
    expected_words = set(expected.split())
    if not expected_words:
        return 1.0
    actual_words = set(actual.split())
    return len(expected_words & actual_words) / len(expected_words)


def _accuracy(expected: str, actual: str) -> float:
    """Combine character and word overlap into a single accuracy score."""
    if not expected:
        return 1.0
    return (_char_overlap(expected, actual) + _word_overlap(expected, actual)) / 2.0


class DefaultBenchmarkRunner:
    """Dependency-free benchmark runner.

    Iterates over the dataset cases, calls ``engine.recognize`` for each and
    scores the result with a simple character/word overlap.  Latency is
    recorded with :func:`time.perf_counter`.  Cases with empty expected text
    always score as perfect so they cannot skew the mean.
    """

    def __init__(self, name: str = "default") -> None:
        """Initialise with a runner name."""
        if not name:
            raise ValueError("name must not be empty")
        self._name = name

    @property
    def name(self) -> str:
        """Return the runner name."""
        return self._name

    def run(
        self,
        dataset: BenchmarkDataset,
        engine: OcrBenchmarkEngine,
        options: dict | None = None,
    ) -> BenchmarkReport:
        """Run *engine* over *dataset* and return a report."""
        if dataset is None:
            raise ValueError("dataset must not be None")
        if engine is None:
            raise ValueError("engine must not be None")
        results: list[BenchmarkResult] = []
        for case in dataset.cases:
            results.append(self._run_case(case, engine))
        return BenchmarkReport(
            engine_name=engine.name,
            dataset_name=dataset.name,
            results=tuple(results),
        )

    def _run_case(self, case: BenchmarkCase, engine: OcrBenchmarkEngine) -> BenchmarkResult:
        start = time.perf_counter()
        actual = engine.recognize(case.image_ref)
        latency = (time.perf_counter() - start) * 1000.0
        accuracy = _accuracy(case.expected_text, actual)
        return BenchmarkResult(
            engine_name=engine.name,
            case_id=case.id,
            accuracy=accuracy,
            latency_ms=latency,
        )


class BenchmarkRunnerRegistry:
    """Registry mapping runner names to :class:`BenchmarkRunner` instances."""

    def __init__(self) -> None:
        self._runners: dict[str, BenchmarkRunner] = {}

    def register(self, runner: BenchmarkRunner) -> None:
        """Register a runner under its ``name``."""
        if not runner.name:
            raise ValueError("runner name must not be empty")
        self._runners[runner.name] = runner

    def get(self, name: str) -> BenchmarkRunner:
        """Return the runner registered under *name*."""
        runner = self._runners.get(name)
        if runner is None:
            raise BenchmarkRunnerNotFoundError(
                f"No benchmark runner registered under '{name}'"
            )
        return runner

    def has(self, name: str) -> bool:
        """Return True if a runner is registered under *name*."""
        return name in self._runners

    def registered_names(self) -> list[str]:
        """Return the registered runner names."""
        return sorted(self._runners)
