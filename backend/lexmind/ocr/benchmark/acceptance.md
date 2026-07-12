# OCR Benchmark Framework - Acceptance

ASCII acceptance criteria for Task 42: OCR Benchmark Framework.

- [x] AC-1: `lexmind/ocr/benchmark/` package exists with `__init__.py` re-exporting public symbols via `__all__`.
- [x] AC-2: `BenchmarkResult` validates accuracy is in `[0, 1]` and `BenchmarkReport.is_acceptable(threshold)` returns whether mean accuracy meets the threshold.
- [x] AC-3: `DefaultBenchmarkRunner` iterates dataset cases, calls `engine.recognize`, computes accuracy via char/word overlap, records latency with `time.perf_counter`, and is safe for empty expected text.
- [x] AC-4: `BenchmarkRunnerRegistry` rejects empty names, `get` raises `BenchmarkRunnerNotFoundError`, and supports `has`/`registered_names`.
- [x] AC-5: `OcrBenchmarkService`/`OcrBenchmarkPlugin` publish `OcrBenchmarkStarted`/`OcrBenchmarkCompleted`/`OcrBenchmarkFailed` via an injected `EventBus` and re-raise on failure.
