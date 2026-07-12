# Table Detection - Acceptance Criteria (Task 38)

## AC-1: Region and result model
- [x] `TableCell` validates non-negative row/column and confidence in [0,1].
- [x] `TableGrid` reports `cell_count` and resolves `cell_at(row, column)`.
- [x] `TableRegion` validates confidence in [0,1].
- [x] `TableDetectionResult` reports `table_count` and `is_empty`.
- [x] `TableDetectionOptions` validates `min_confidence` and exposes `keeps`.

## AC-2: Detector contract and registry
- [x] `TableDetector` is a `runtime_checkable` Protocol (`name`, `detect`).
- [x] `RuleBasedTableDetector` composes a `LayoutAnalyzer` to find TABLE
      regions; with `detect_cells=True` it emits a single-cell grid, with
      `detect_cells=False` it emits an empty grid; honours `min_confidence`;
      rejects a `None` analyzer and empty input.
- [x] `DetectionTableDetector` wraps a `TableDetectionEngine` and filters its
      output by the options; rejects a `None` engine and empty input.
- [x] `TableDetectorRegistry.register` rejects empty names; `get` raises
      `TableDetectorNotFoundError` for unknown names; `has` / `registered_names`
      reflect state.

## AC-3: Service orchestration
- [x] `TableDetectionService.detect` resolves a detector (explicit name,
      configured default, or first registered), runs it and returns a
      `TableDetectionResult`.
- [x] `TableDetectionStarted` / `TableDetectionCompleted` are emitted; on
      failure `TableDetectionFailed` is emitted and the error propagates.
- [x] No registered detector raises `TableDetectorNotFoundError`.

## AC-4: Plugin integration
- [x] `TableDetectionPlugin` declares `PluginCapability.TABLE_DETECTION`.
- [x] By default it ships with a `RuleBasedTableDetector` (using a
      `RuleBasedLayoutAnalyzer`).
- [x] `detect` and `register_detector` delegate to the service; `start` /
      `stop` transition state.

## AC-5: Quality gates
- [x] Model work is isolated behind `TableDetectionEngine`; the default path
      has no external dependency (it reuses the layout framework).
- [x] Code is ASCII-only and passes `ruff`.
- [x] Covered by `tests/unit/test_table_detection.py` (types, detectors,
      registry, service, events, plugin).
