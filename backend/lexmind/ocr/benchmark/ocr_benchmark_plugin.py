"""OCR benchmark plugin.

Exposes the OCR benchmark framework through the plugin system.  Wraps an
:class:`OcrBenchmarkService` (backed by a
:class:`~lexmind.ocr.benchmark.benchmark_runner.BenchmarkRunnerRegistry`) and
declares :class:`PluginCapability.OCR_BENCHMARK`.  Ships the
dependency-free :class:`DefaultBenchmarkRunner`.
"""

from __future__ import annotations

from lexmind.events.event_bus import EventBus
from lexmind.ocr.benchmark.benchmark_runner import (
    BenchmarkRunner,
    BenchmarkRunnerRegistry,
    OcrBenchmarkEngine,
)
from lexmind.ocr.benchmark.benchmark_types import BenchmarkDataset, BenchmarkReport
from lexmind.ocr.benchmark.ocr_benchmark import OcrBenchmarkService
from lexmind.plugins.plugin import BasePlugin
from lexmind.plugins.plugin_capability import PluginCapability


class OcrBenchmarkPlugin(BasePlugin):
    """Plugin providing OCR benchmarking."""

    def __init__(
        self,
        registry: BenchmarkRunnerRegistry | None = None,
        event_bus: EventBus | None = None,
        plugin_id: str = "ocr-benchmark",
    ) -> None:
        """Initialise the plugin.

        Args:
            registry: Runner registry.  Defaults to a registry pre-populated
                with the dependency-free :class:`DefaultBenchmarkRunner`.
            event_bus: Optional bus for lifecycle events.
            plugin_id: Explicit plugin id.
        """
        super().__init__(
            id=plugin_id,
            name="OCR Benchmark",
            version="1.0.0",
            description="Runs benchmarks of OCR engines over labelled datasets.",
            capabilities=(PluginCapability.OCR_BENCHMARK,),
        )
        self._service = OcrBenchmarkService(registry, event_bus=event_bus)

    @property
    def service(self) -> OcrBenchmarkService:
        """Return the underlying benchmark service."""
        return self._service

    @property
    def registry(self) -> BenchmarkRunnerRegistry:
        """Return the runner registry."""
        return self._service.registry

    def run_benchmark(
        self,
        dataset: BenchmarkDataset,
        engine: OcrBenchmarkEngine,
        runner_name: str | None = None,
        options: dict | None = None,
    ) -> BenchmarkReport:
        """Benchmark *engine* over *dataset* using the service."""
        return self._service.run_benchmark(
            dataset,
            engine,
            runner_name=runner_name,
            options=options,
        )

    def register_runner(self, runner: BenchmarkRunner) -> None:
        """Register an additional runner (e.g. a model-backed one)."""
        self._service.registry.register(runner)

    def start(self) -> None:
        """Activate the plugin."""
        super().start()

    def stop(self) -> None:
        """Deactivate the plugin."""
        super().stop()
