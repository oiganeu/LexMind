# Table Detection (Task 38)

The **Table Detection** framework locates tables on a document page and
builds their cell grids through an engine-agnostic detector contract.  The
default :class:`RuleBasedTableDetector` *composes with the layout framework*:
it asks an injected :class:`~lexmind.layout.layout_analyzer.LayoutAnalyzer`
for ``TABLE`` regions and turns each into a
:class:`~lexmind.table_detection.table_types.TableRegion`.  Model-backed
detectors plug in via the registry.  The orchestrating service resolves
detectors and emits lifecycle events.

## Architecture

```
TableDetectionOptions -> declarative filters (min_confidence, detect_cells)
        |
        v
TableDetectionService  (resolves detector, emits events)
        |
        v
TableDetectorRegistry -> name -> TableDetector
        |                        |
        |                        +-- RuleBasedTableDetector (uses a LayoutAnalyzer)
        |                        +-- DetectionTableDetector (wraps a
        |                             TableDetectionEngine)
        v
TableDetectionResult (page_number, tables[TableRegion], detector)
```

## Components (`lexmind/table_detection/`)

* `table_types` -> `TableCell` (row/column + bbox + text), `TableGrid`
  (rows/columns/cells, `cell_at`), `TableRegion`, `TableDetectionResult`,
  `TableDetectionOptions` (with `keeps()` filtering).
* `table_detector` -> `TableDetector` Protocol, `TableDetectionEngine`
  Protocol, `RuleBasedTableDetector` (composes layout analysis),
  `DetectionTableDetector` (wraps an engine), and `TableDetectorRegistry` /
  `TableDetectorNotFoundError`.
* `table_detection` -> `TableDetectionService` (the orchestrator) with event
  publishing and error wrapping.
* `table_detection_events` -> `TableDetectionStarted`,
  `TableDetectionCompleted`, `TableDetectionFailed`.
* `table_plugin` -> `TableDetectionPlugin` declaring
  `PluginCapability.TABLE_DETECTION`.

## Usage

```python
plugin = TableDetectionPlugin()                 # ships with rule-based detector
result = plugin.detect(image_bytes, TableDetectionOptions(
    min_confidence=0.5,
    detect_cells=True,
))

# or register a model-backed detector:
plugin.register_detector(DetectionTableDetector(my_engine))
```

## Design notes

* **Composes with layout**: the rule-based path reuses a `LayoutAnalyzer`, so
  table detection builds directly on Task 37 with no new dependencies.
* **Engine isolation**: model work is confined to `TableDetectionEngine`
  implementations; the framework depends only on the Protocol.
* **No global state / singletons**: registry, service and event bus are
  injected.
