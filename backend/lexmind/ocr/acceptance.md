# OCR Engine Framework - Acceptance Criteria (Task 31)

## AC-1: Provider contract
- [x] `OCRProvider` is a `runtime_checkable` Protocol with `name`,
      `supports(mime_type)` and `recognize(image_data, language, mime_type)`.
- [x] `OCRResult` / `OCRPageResult` are immutable, engine-agnostic value
      objects with validated confidence in [0, 1].

## AC-2: Provider selection (dispatcher)
- [x] `OCRDispatcher.register` adds providers and auto-selects a default.
- [x] `select` resolves by explicit name, then default, then MIME support.
- [x] Unknown name or unsupported MIME raises `OCRProviderNotFoundError`.
- [x] `unregister` keeps the default consistent.

## AC-3: Pipeline orchestration
- [x] `OCRPipeline.execute` selects a provider, loads input from the
      injected `StorageManager`, recognises, persists and emits events.
- [x] `OCRStarted` is emitted before recognition; `OCRCompleted` after a
      successful run with page count and confidence.
- [x] On failure `OCRFailed` is emitted and the error is re-raised.
- [x] `OCRRequest` validation rejects empty workspace/document/source URI.

## AC-4: Artifact persistence
- [x] `OCRArtifactWriter.write` stores text + JSON artifacts via the
      injected `StorageManager` and returns the text artifact URI.
- [x] JSON serialisation preserves text, confidence, language, provider,
      pages and metadata.

## AC-5: Tesseract engine (concrete provider)
- [x] `TesseractConfig` validates psm/oem/timeout/min_confidence/language
      and exposes `to_config_string` / `with_language`.
- [x] `TesseractOCRProvider` satisfies `OCRProvider`: `name == "tesseract"`,
      `supports` the expected MIME set, and `recognize` returns a normalised
      `OCRResult` using an injected engine.
- [x] `recognize` rejects empty `image_data` and honours language overrides.
- [x] `OCRResultMapper` groups words per page and normalises confidence.
- [x] `PytesseractEngine` imports pytesseract/Pillow lazily so the module is
      importable without the native binary.

## AC-6: Quality gates
- [x] Engine specifics are isolated in `providers/`; the orchestration layer
      depends only on the `OCRProvider` contract.
- [x] All collaborators are injected (no singletons / globals).
- [x] Code is ASCII-only and passes `ruff`.
- [x] The injectable architecture (protocol, dispatcher, pipeline, result,
      mapper, config, provider) is fully unit-tested; only the native
      `PytesseractEngine` binding (requires the Tesseract binary) is outside
      unit coverage by design.
