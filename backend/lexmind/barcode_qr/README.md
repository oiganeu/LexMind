# Barcode & QR Detection (Task 39)

The **Barcode & QR Detection** framework locates machine-readable codes on a
document page and decodes their payloads through an engine-agnostic detector
contract.  The default :class:`RuleBasedBarcodeDetector` is *dependency-free*:
it returns an empty result, acting as a safe registration target until a real
code-reading engine is injected.  Model-backed readers plug in via
:class:`DetectionBarcodeDetector` (which wraps a
:class:`~lexmind.barcode_qr.barcode_qr_detector.BarcodeDetectionEngine`) and the
registry.  The orchestrating service resolves detectors and emits lifecycle
events.

## Architecture

```
BarcodeDetectionOptions -> declarative filters (min_confidence, formats)
        |
        v
BarcodeDetectionService  (resolves detector, emits events)
        |
        v
BarcodeDetectorRegistry -> name -> BarcodeDetector
        |                        |
        |                        +-- RuleBasedBarcodeDetector (empty stub,
        |                             dependency-free default)
        |                        +-- DetectionBarcodeDetector (wraps a
        |                             BarcodeDetectionEngine)
        v
BarcodeDetectionResult (page_number, regions[BarcodeRegion], detector)
```

## Components (`lexmind/barcode_qr/`)

* `barcode_qr_types` -> `BarcodeFormat` (StrEnum: QR, CODE128, EAN13, CODE39,
  DATA_MATRIX, PDF417, AZTEC, UNKNOWN), `BarcodeRegion` (bbox + format +
  payload + confidence, with validation), `BarcodeDetectionResult`
  (`code_count`, `is_empty`), and `BarcodeDetectionOptions` (with `keeps()`
  filtering by confidence and format).
* `barcode_qr_detector` -> `BarcodeDetector` Protocol, `BarcodeDetectionEngine`
  Protocol, `RuleBasedBarcodeDetector` (empty stub), `DetectionBarcodeDetector`
  (wraps an engine and filters), and `BarcodeDetectorRegistry` /
  `BarcodeDetectorNotFoundError`.
* `barcode_qr_detection` -> `BarcodeDetectionService` (the orchestrator) with
  event publishing and error wrapping.
* `barcode_qr_detection_events` -> `BarcodeDetectionStarted`,
  `BarcodeDetectionCompleted`, `BarcodeDetectionFailed`.
* `barcode_qr_plugin` -> `BarcodeDetectionPlugin` declaring
  `PluginCapability.BARCODE_QR_DETECTION`.

## Usage

```python
plugin = BarcodeDetectionPlugin()                 # ships with rule-based detector
result = plugin.detect(image_bytes, BarcodeDetectionOptions(
    min_confidence=0.5,
    formats=(BarcodeFormat.QR,),
))

# or register a model-backed detector:
plugin.register_detector(DetectionBarcodeDetector(my_engine))
```

## Design notes

* **Dependency-free default**: the rule-based path has no external dependency;
  it returns an empty result, so the framework is fully usable before any
  code-reading engine is wired in.
* **Engine isolation**: reader work is confined to `BarcodeDetectionEngine`
  implementations; the framework depends only on the Protocol.
* **No global state / singletons**: registry, service and event bus are
  injected.
* **Reuses layout types**: regions reuse
  `lexmind.layout.layout_types.BoundingBox` for normalised coordinates.
