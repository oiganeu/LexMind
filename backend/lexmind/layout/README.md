# Layout Analysis (Task 37)

The **Layout Analysis** framework detects the structural regions of a
document page (text blocks, tables, figures, headers, ...) through an
engine-agnostic analyzer contract.  A dependency-free `RuleBasedLayoutAnalyzer`
ships by default, while model-backed analyzers can be injected via the
registry.  The orchestrating service resolves analyzers, optionally merges
overlapping regions and emits lifecycle events.

## Architecture

```
LayoutAnalysisOptions -> declarative filters (region types, min_confidence, merge)
        |
        v
LayoutAnalysisService  (resolves analyzer, merges, emits events)
        |
        v
LayoutAnalyzerRegistry -> name -> LayoutAnalyzer
        |                        |
        |                        +-- RuleBasedLayoutAnalyzer (no deps, testable)
        |                        +-- DetectionLayoutAnalyzer (wraps a
        |                             LayoutDetectionEngine)
        v
LayoutResult (page_number, regions[LayoutRegion], analyzer)
```

## Components (`lexmind/layout/`)

* `layout_types` -> `RegionType` (enum), `BoundingBox` (normalised, validated),
  `LayoutRegion`, `LayoutResult`, `LayoutAnalysisOptions` (with `keeps()`
  filtering).
* `layout_analyzer` -> `LayoutAnalyzer` Protocol, `LayoutDetectionEngine`
  Protocol, `RuleBasedLayoutAnalyzer`, `DetectionLayoutAnalyzer`, and
  `LayoutAnalyzerRegistry` / `LayoutAnalyzerNotFoundError`.
* `layout_analysis` -> `LayoutAnalysisService` (the orchestrator) with
  overlapping-region merge and event publishing.
* `layout_events` -> `LayoutAnalysisStarted`, `LayoutAnalysisCompleted`,
  `LayoutAnalysisFailed`.
* `layout_plugin` -> `LayoutAnalysisPlugin` declaring
  `PluginCapability.LAYOUT_ANALYSIS`.

## Usage

```python
plugin = LayoutAnalysisPlugin()                 # ships with rule-based analyzer
result = plugin.analyze(image_bytes, LayoutAnalysisOptions(
    region_types=(RegionType.TABLE, RegionType.TEXT),
    min_confidence=0.5,
    merge_overlapping=True,
))

# or register a model-backed analyzer:
plugin.register_analyzer(DetectionLayoutAnalyzer(my_engine))
```

## Design notes

* **Engine isolation**: pixel/model work is confined to `LayoutDetectionEngine`
  implementations; the framework depends only on the Protocols.
* **Default without dependencies**: `RuleBasedLayoutAnalyzer` is fully usable
  and tested with no external library.
* **Composable**: extra analyzers register into the shared registry and are
  selected by name, with no code changes to the service.
* **No global state / singletons**: registry, service and event bus are
  injected.
