# Language Detection - Acceptance Criteria (Task 40)

## AC-1: Type model validation
- [x] `DetectedLanguage` validates non-empty code and confidence in [0,1].
- [x] `LanguageDetectionOptions` validates min_confidence and exposes `keeps()`.
- [x] `LanguageDetectionResult` reports `top_language` and `is_empty`.

## AC-2: Detector contract and registry
- [x] `LanguageDetector` is a `runtime_checkable` Protocol (`name`, `detect`).
- [x] `RuleBasedLanguageDetector` returns a single hardcoded language with full
      confidence; raises `ValueError` on empty input.
- [x] `DetectionLanguageDetector` wraps a `LanguageDetectionEngine` and filters
      its output by the options; rejects a `None` engine and empty input.
- [x] `LanguageDetectorRegistry.register` rejects empty names; `get` raises
      `LanguageDetectorNotFoundError` for unknown names; `has` /
      `registered_names` reflect state.

## AC-3: Service orchestration
- [x] `LanguageDetectionService.detect` resolves a detector (explicit name,
      configured default, or first registered), runs it and returns a
      `LanguageDetectionResult`.
- [x] `LanguageDetectionStarted` / `LanguageDetectionCompleted` are emitted;
      on failure `LanguageDetectionFailed` is emitted and the error propagates.
- [x] No registered detector raises `LanguageDetectorNotFoundError`.

## AC-4: Plugin integration
- [x] `LanguageDetectionPlugin` declares `PluginCapability.LANGUAGE_DETECTION`.
- [x] By default it ships with a `RuleBasedLanguageDetector`.
- [x] `detect` and `register_detector` delegate to the service; `start` /
      `stop` transition state.

## AC-5: Quality gates
- [x] Model work is isolated behind `LanguageDetectionEngine`; the default
      path has no external dependency.
- [x] Code is ASCII-only and passes `ruff`.
- [x] Covered by `tests/unit/test_language_detection.py` (types, detectors,
      registry, service, events, plugin).
