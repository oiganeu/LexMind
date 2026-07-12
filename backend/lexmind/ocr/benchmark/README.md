# OCR Benchmark Framework

The OCR Benchmark Framework (`lexmind.ocr.benchmark`) measures how accurately an
OCR engine reproduces known reference texts, and how fast it runs.  It mirrors
the structure of `lexmind.table_detection`: value objects, engine/runner
contracts, a registry, an orchestrating service, and a plugin.

## Components

- `benchmark_types.py`: `BenchmarkCase`, `BenchmarkDataset`, `BenchmarkResult`,
  `BenchmarkReport` (with `mean_accuracy`, `mean_latency`, `is_acceptable`).
- `benchmark_runner.py`: `OcrBenchmarkEngine` and `BenchmarkRunner` protocols,
  the dependency-free `DefaultBenchmarkRunner` (char/word overlap scoring +
  `time.perf_counter` latency), `BenchmarkRunnerRegistry`, and
  `BenchmarkRunnerNotFoundError`.
- `ocr_benchmark.py`: `OcrBenchmarkService` orchestrates runs and publishes
  lifecycle events.
- `ocr_benchmark_events.py`: `OcrBenchmarkStarted`, `OcrBenchmarkCompleted`,
  `OcrBenchmarkFailed`.
- `ocr_benchmark_plugin.py`: `OcrBenchmarkPlugin` declaring
  `PluginCapability.OCR_BENCHMARK`.

## Scoring

The default runner scores accuracy as the mean of character-set overlap and
word-set overlap between expected and actual text, both in `[0, 1]`.  Cases with
empty expected text always score as perfect so they cannot skew the mean.

## Usage

```python
from lexmind.ocr.benchmark import OcrBenchmarkPlugin, BenchmarkDataset, BenchmarkCase

plugin = OcrBenchmarkPlugin()
dataset = BenchmarkDataset(
    name="samples",
    cases=(BenchmarkCase(id="c1", expected_text="hello world", image_ref="i1"),),
)
report = plugin.run_benchmark(dataset, my_engine)
print(report.mean_accuracy, report.is_acceptable(0.9))
```
