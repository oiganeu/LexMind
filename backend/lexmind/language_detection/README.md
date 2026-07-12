# Language Detection (Task 40)

The **Language Detection** framework identifies the natural language(s) present
in text through an engine-agnostic detector contract.  The default
:class:`RuleBasedLanguageDetector` is a no-dependency baseline.  Model-backed
detectors plug in via the registry.  The orchestrating
:class:`LanguageDetectionService` resolves detectors and emits lifecycle events.

## Architecture

```
LanguageDetectionOptions -> declarative filters (candidate_codes, min_confidence)
        |
        v
LanguageDetectionService  (resolves detector, emits events)
        |
        v
LanguageDetectorRegistry -> name -> LanguageDetector
        |                            |
        |                            +-- RuleBasedLanguageDetector (no deps)
        |                            +-- DetectionLanguageDetector (wraps a
        |                                 LanguageDetectionEngine)
        v
LanguageDetectionResult (text_or_page, languages[DetectedLanguage], detector)
```

## Components (`lexmind/language_detection/`)

* `language_detection_types` -> `DetectedLanguage` (code + confidence with
  validation), `LanguageDetectionOptions` (candidate_codes filter,
  min_confidence, `keeps()`), `LanguageDetectionResult` (text_or_page,
  languages, detector, `top_language`, `is_empty`).
* `language_detector` -> `LanguageDetector` Protocol, `LanguageDetectionEngine`
  Protocol, `RuleBasedLanguageDetector` (no-dependency default),
  `DetectionLanguageDetector` (wraps an engine), and
  `LanguageDetectorRegistry` / `LanguageDetectorNotFoundError`.
* `language_detection` -> `LanguageDetectionService` (the orchestrator) with
  event publishing and error wrapping.
* `language_detection_events` -> `LanguageDetectionStarted`,
  `LanguageDetectionCompleted`, `LanguageDetectionFailed`.
* `language_detection_plugin` -> `LanguageDetectionPlugin` declaring
  `PluginCapability.LANGUAGE_DETECTION`.

## Usage

```python
plugin = LanguageDetectionPlugin()               # ships with rule-based detector
result = plugin.detect("Hello, world!")
print(result.top_language.code)                  # "en"

# or register a model-backed detector:
plugin.register_detector(DetectionLanguageDetector(my_engine))
```

## Design notes

* **No-dependency default**: the rule-based path returns a hardcoded result
  with no external dependency.
* **Engine isolation**: model work is confined to `LanguageDetectionEngine`
  implementations; the framework depends only on the Protocol.
* **No global state / singletons**: registry, service and event bus are
  injected.
* **Filtering**: `LanguageDetectionOptions.keeps()` filters by both
  `candidate_codes` and `min_confidence`, applied consistently by both
  `DetectionLanguageDetector` and the service.
