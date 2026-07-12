"""OCR benchmark framework.

Benchmarks OCR engines against labelled datasets.  The
:class:`~lexmind.ocr.benchmark.benchmark_runner.DefaultBenchmarkRunner` scores
an engine with a simple character/word overlap and records latency, so it works
with no external dependency.  The orchestrating
:class:`~lexmind.ocr.benchmark.ocr_benchmark.OcrBenchmarkService` resolves
runners from the registry and emits lifecycle events.  The
:class:`~lexmind.ocr.benchmark.ocr_benchmark_plugin.OcrBenchmarkPlugin` exposes
everything through the plugin system under
:class:`PluginCapability.OCR_BENCHMARK`.
"""

from __future__ import annotations

from lexmind.ocr.benchmark.benchmark_runner import (
    BenchmarkRunner,
    BenchmarkRunnerNotFoundError,
    BenchmarkRunnerRegistry,
    DefaultBenchmarkRunner,
    OcrBenchmarkEngine,
)
from lexmind.ocr.benchmark.benchmark_types import (
    BenchmarkCase,
    BenchmarkDataset,
    BenchmarkReport,
    BenchmarkResult,
)
from lexmind.ocr.benchmark.ocr_benchmark import OcrBenchmarkService
from lexmind.ocr.benchmark.ocr_benchmark_events import (
    OcrBenchmarkCompleted,
    OcrBenchmarkFailed,
    OcrBenchmarkStarted,
)
from lexmind.ocr.benchmark.ocr_benchmark_plugin import OcrBenchmarkPlugin

__all__ = [
    "BenchmarkCase",
    "BenchmarkDataset",
    "BenchmarkReport",
    "BenchmarkResult",
    "BenchmarkRunner",
    "BenchmarkRunnerNotFoundError",
    "BenchmarkRunnerRegistry",
    "DefaultBenchmarkRunner",
    "OcrBenchmarkCompleted",
    "OcrBenchmarkEngine",
    "OcrBenchmarkFailed",
    "OcrBenchmarkPlugin",
    "OcrBenchmarkService",
    "OcrBenchmarkStarted",
]
