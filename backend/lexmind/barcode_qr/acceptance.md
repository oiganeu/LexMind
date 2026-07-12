# Barcode & QR Detection - Acceptance Criteria (Task 39)

## AC-1: Region and result model
- [x] `BarcodeFormat` is a `StrEnum` covering QR, CODE128, EAN13, CODE39,
      DATA_MATRIX, PDF417, AZTEC, UNKNOWN.
- [x] `BarcodeRegion` validates its `BarcodeFormat`, string `payload` and
      confidence in [0,1]; it reuses `BoundingBox` for coordinates.
- [x] `BarcodeDetectionResult` reports `code_count` and `is_empty`.
- [x] `BarcodeDetectionOptions` validates `min_confidence`, validates the
      `formats` tuple, and exposes `keeps` (confidence + format filtering).

## AC-2: Detector contract and registry
- [x] `BarcodeDetector` is a `runtime_checkable` Protocol (`name`, `detect`).
- [x] `RuleBasedBarcodeDetector` is dependency-free and returns an empty
      result; it rejects empty input.
- [x] `DetectionBarcodeDetector` wraps a `BarcodeDetectionEngine` and filters
      its output by the options; rejects a `None` engine and empty input.
- [x] `BarcodeDetectorRegistry.register` rejects empty names; `get` raises
      `BarcodeDetectorNotFoundError` for unknown names; `has` /
      `registered_names` reflect state.

## AC-3: Service orchestration
- [x] `BarcodeDetectionService.detect` resolves a detector (explicit name,
      configured default, or first registered), runs it and returns a
      `BarcodeDetectionResult`.
- [x] `BarcodeDetectionStarted` / `BarcodeDetectionCompleted` are emitted; on
      failure `BarcodeDetectionFailed` is emitted and the error propagates.
- [x] No registered detector raises `BarcodeDetectorNotFoundError`.

## AC-4: Plugin integration
- [x] `BarcodeDetectionPlugin` declares `PluginCapability.BARCODE_QR_DETECTION`.
- [x] By default it ships with a `RuleBasedBarcodeDetector`.
- [x] `detect` and `register_detector` delegate to the service; `start` /
      `stop` transition state.

## AC-5: Quality gates
- [x] Reader work is isolated behind `BarcodeDetectionEngine`; the default path
      has no external dependency.
- [x] Code is ASCII-only and passes `ruff`.
- [x] Covered by `tests/unit/test_barcode_qr.py` (types, detectors, registry,
      service, events, plugin).
