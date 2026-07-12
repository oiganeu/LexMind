# OCR Engine Framework (Task 31)

The **OCR Engine Framework** provides engine-agnostic optical character
recognition for LexMind. Concrete engines (Tesseract today, PaddleOCR /
cloud OCR tomorrow) are isolated behind a single plugin contract, while the
orchestration layer stays completely unaware of any specific engine.

The framework was introduced in tasks 12-25; this task documents and
completes its test surface.

## Layered design

```
            OCRProvider (Protocol)  <-- engine contract
                 ^
   TesseractOCRProvider (concrete, injectable engine)
                 |
   OCRDispatcher  ->  selects provider by name / default / MIME
   OCRPipeline    ->  orchestrates: select -> load -> recognize -> persist -> events
   OCRArtifactWriter -> persists OCRResult via StorageManager
   OCRResult / OCRPageResult -> engine-agnostic output value objects
   OCRStarted / OCRCompleted / OCRFailed -> lifecycle events
```

## Component reference

### `OCRProvider` (`ocr_provider.py`)
The contract every OCR engine plugin satisfies: `name`, `supports(mime_type)`
and `recognize(image_data, language, mime_type) -> OCRResult`. It is a
`runtime_checkable` Protocol, so no base class coupling is required.

### `OCRResult` / `OCRPageResult` (`ocr_result.py`)
Immutable, engine-neutral recognition output. `OCRResult` aggregates full
text, overall confidence (0-100 normalised to [0,1]), language, provider
name, per-page results and opaque metadata. Validation enforces confidence
bounds.

### `OCRDispatcher` (`ocr_dispatcher.py`)
A dependency-injected registry that selects a provider: by explicit name,
then configured default, then first provider that `supports` the requested
MIME type. Raises `OCRProviderNotFoundError` when nothing matches.

### `OCRPipeline` (`ocr_pipeline.py`)
End-to-end orchestrator. `OCRPipeline.execute(OCRRequest)`:
1. selects a provider via the dispatcher;
2. emits `OCRStarted`;
3. loads input bytes from the injected `StorageManager`;
4. calls `provider.recognize(...)`;
5. persists output via `OCRArtifactWriter`;
6. emits `OCRCompleted` (or `OCRFailed` on error, then re-raises).

Input is described by `OCRRequest` (workspace/document/source URI/language/
MIME/optional provider); output is `OCROutcome` (result + artifact URI +
provider name).

### `OCRArtifactWriter` (`ocr_artifact_writer.py`)
Serialises an `OCRResult` (text + JSON) and stores both artifacts through
the injected `StorageManager`. No direct filesystem access.

### Tesseract provider (`providers/`)
* `TesseractConfig` — frozen, validated config (language, psm, oem, timeout,
  min_confidence) with `to_config_string` / `with_language`.
* `TesseractEngine` — Protocol for the actual recognition call.
* `PytesseractEngine` — default engine backed by `pytesseract` + `Pillow`,
  **imported lazily** so the module is importable without the native binary.
* `OCRResultMapper` — converts Tesseract's per-word raw output into the
  normalised `OCRResult` (per-page grouping, mean confidence normalised to
  [0,1], optional low-confidence filtering).
* `TesseractOCRProvider` — implements `OCRProvider`; all engine specifics
  are confined here and made testable via an injected `TesseractEngine`.

## Design notes

* **Engine isolation**: every engine-specific concern lives in `providers/`;
  the rest of the platform depends only on the `OCRProvider` contract.
* **Dependency injection**: the pipeline, dispatcher, writer and provider
  all receive collaborators via constructors — nothing is a singleton or
  global.
* **Framework-only core**: the orchestration, dispatcher, result, mapper and
  config contain no infrastructure imports and are fully unit-tested; only
  the native `PytesseractEngine` binding (which requires the Tesseract
  binary + pytesseract/Pillow) is excluded from unit coverage by design.
* ASCII-only, ruff-clean.
