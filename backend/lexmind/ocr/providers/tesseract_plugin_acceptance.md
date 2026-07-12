# Tesseract Plugin - Acceptance Criteria (Task 33)

## AC-1: Plugin construction
- [x] `TesseractPlugin(dispatcher)` builds a `TesseractOCRProvider` and is an
      `OCRProviderPlugin`.
- [x] Default plugin id is `tesseract-ocr` and `PluginCapability.OCR` is
      declared.
- [x] A custom `TesseractConfig` is accepted and exposed via
      `.tesseract_config`.
- [x] A custom `TesseractEngine` may be injected (defaults to
      `PytesseractEngine`).
- [x] A `None` dispatcher is rejected.

## AC-2: Lifecycle and registration
- [x] `start()` registers the `tesseract` provider into the dispatcher and
      moves the plugin to the STARTED state.
- [x] `stop()` unregisters the provider.
- [x] After start, the provider is selectable by name (`tesseract`) and
      recognises via the injected engine, returning an `OCRResult`.

## AC-3: Capability coverage
- [x] `provider.supports` returns True for the Tesseract MIME set
      (png/jpeg/tiff/bmp/pdf) and False otherwise.

## AC-4: Testability / separation
- [x] The plugin and provider are unit-tested with a stub engine; the native
      `PytesseractEngine` binding is the only part outside unit coverage.
- [x] No global state: registration is per-dispatcher via injection.

## AC-5: Quality gates
- [x] Code is ASCII-only and passes `ruff`.
- [x] Covered by `tests/unit/test_tesseract_plugin.py`.
