# Layout Analysis - Acceptance Criteria (Task 37)

## AC-1: Region and result model
- [x] `RegionType` enumerates the supported region semantics.
- [x] `BoundingBox` validates all coordinates are in [0, 1].
- [x] `LayoutRegion` validates confidence in [0, 1].
- [x] `LayoutResult` reports `region_count` and `is_empty`.
- [x] `LayoutAnalysisOptions.keeps` filters by region type and confidence;
      `min_confidence` is validated.

## AC-2: Analyzer contract and registry
- [x] `LayoutAnalyzer` is a `runtime_checkable` Protocol (`name`, `analyze`).
- [x] `RuleBasedLayoutAnalyzer` returns a full-page text region and honours
      the configured filters; rejects empty image data.
- [x] `DetectionLayoutAnalyzer` wraps a `LayoutDetectionEngine` and filters
      its output by the options; rejects a `None` engine and empty input.
- [x] `LayoutAnalyzerRegistry.register` rejects empty names; `get` raises
      `LayoutAnalyzerNotFoundError` for unknown names; `has` / `registered_names`
      reflect state.

## AC-3: Service orchestration
- [x] `LayoutAnalysisService.analyze` resolves an analyzer (explicit name,
      configured default, or first registered), runs it and returns a
      `LayoutResult`.
- [x] `merge_overlapping` drops lower-confidence regions contained in
      higher-confidence ones.
- [x] `LayoutAnalysisStarted` / `LayoutAnalysisCompleted` are emitted; on
      failure `LayoutAnalysisFailed` is emitted and the error propagates.
- [x] No registered analyzer raises `LayoutAnalyzerNotFoundError`.

## AC-4: Plugin integration
- [x] `LayoutAnalysisPlugin` declares `PluginCapability.LAYOUT_ANALYSIS`.
- [x] By default it ships with the `RuleBasedLayoutAnalyzer` registered.
- [x] `analyze` and `register_analyzer` delegate to the service; `start` /
      `stop` transition state.

## AC-5: Quality gates
- [x] Model work is isolated behind `LayoutDetectionEngine`; the framework's
      default path has no external dependency.
- [x] Code is ASCII-only and passes `ruff`.
- [x] Covered by `tests/unit/test_layout_analysis.py` (types, analyzers,
      registry, service, merge, events, plugin).
