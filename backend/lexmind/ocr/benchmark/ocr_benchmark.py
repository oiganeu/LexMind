"""OCR benchmark service.

The :class:`OcrBenchmarkService` orchestrates benchmark runs: it resolves a
runner from the registry, executes it against a dataset/engine pair and
publishes lifecycle events.  On failure it emits an
:class:`OcrBenchmarkFailed` event and re-raises so callers can react.
"""

from __future__ import annotations

import structlog

from lexmind.events.event_bus import EventBus
from lexmind.ocr.benchmark.benchmark_runner import (
    BenchmarkRunner,
    BenchmarkRunnerNotFoundError,
    BenchmarkRunnerRegistry,
    DefaultBenchmarkRunner,
    OcrBenchmarkEngine,
)
from lexmind.ocr.benchmark.benchmark_types import BenchmarkDataset, BenchmarkReport
from lexmind.ocr.benchmark.ocr_benchmark_events import (
    OcrBenchmarkCompleted,
    OcrBenchmarkFailed,
    OcrBenchmarkStarted,
)

logger = structlog.get_logger(__name__)


class OcrBenchmarkService:
    """Orchestrates OCR benchmarking runs against a runner registry."""

    def __init__(
        self,
        registry: BenchmarkRunnerRegistry | None = None,
        event_bus: EventBus | None = None,
        default_runner: str | None = None,
    ) -> None:
        """Initialise with a registry and optional bus/default.

        Args:
            registry: Registry of available runners.  Defaults to a registry
                pre-populated with the dependency-free
                :class:`DefaultBenchmarkRunner`.
            event_bus: Optional bus for lifecycle events.
            default_runner: Name of the runner to use when none is requested.
                Defaults to the first registered runner.
        """
        if registry is None:
            registry = BenchmarkRunnerRegistry()
            registry.register(DefaultBenchmarkRunner())
        self._registry = registry
        self._event_bus = event_bus
        self._default = default_runner

    @property
    def registry(self) -> BenchmarkRunnerRegistry:
        """Return the runner registry."""
        return self._registry

    def _resolve(self, runner_name: str | None) -> BenchmarkRunner:
        name = runner_name or self._default or self._registry.registered_names()[0]
        return self._registry.get(name)

    def _emit(self, event: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event)

    def run_benchmark(
        self,
        dataset: BenchmarkDataset,
        engine: OcrBenchmarkEngine,
        runner_name: str | None = None,
        options: dict | None = None,
    ) -> BenchmarkReport:
        """Run a benchmark for *engine* over *dataset*.

        Args:
            dataset: The benchmark dataset.
            engine: The OCR engine under test.
            runner_name: Optional explicit runner name.
            options: Optional runner-specific options.

        Returns:
            A :class:`BenchmarkReport`.

        Raises:
            BenchmarkRunnerNotFoundError: If no runner can be resolved.
        """
        self._emit(
            OcrBenchmarkStarted(
                engine_name=engine.name,
                dataset_name=dataset.name,
            )
        )
        try:
            runner = self._resolve(runner_name)
        except IndexError as exc:
            self._emit(
                OcrBenchmarkFailed(
                    engine_name=engine.name,
                    dataset_name=dataset.name,
                    error_message=str(exc),
                )
            )
            raise BenchmarkRunnerNotFoundError(
                "No benchmark runner registered"
            ) from exc

        try:
            report = runner.run(dataset, engine, options=options)
            self._emit(
                OcrBenchmarkCompleted(
                    engine_name=report.engine_name,
                    dataset_name=report.dataset_name,
                    mean_accuracy=report.mean_accuracy,
                    mean_latency=report.mean_latency,
                )
            )
            return report
        except Exception as exc:  # noqa: BLE001 - surface as benchmark failure
            self._emit(
                OcrBenchmarkFailed(
                    engine_name=engine.name,
                    dataset_name=dataset.name,
                    error_message=str(exc),
                )
            )
            logger.error("ocr_benchmark_failed", engine=engine.name, error=str(exc))
            raise
