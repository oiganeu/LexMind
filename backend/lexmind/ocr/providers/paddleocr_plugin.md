# PaddleOCR Plugin (Task 34)

The **PaddleOCR Plugin** adds PaddleOCR — a multilingual OCR engine with
strong support for non-Latin scripts — as a LexMind OCR provider. It follows
exactly the architecture established by the Tesseract provider/plugin
(Tasks 31-33): engine-specific code is isolated, recognition is injected
behind a Protocol, and the provider is packaged as a plugin that registers
with a shared `OCRDispatcher`.

## Components (`lexmind/ocr/providers/paddleocr_provider.py`)

* `PaddleOCRConfig` — frozen, validated config (`language`, `use_angle_cls`,
  `det_db_box_thresh`, `drop_score`) with `to_kwargs()` (for the paddleocr
  call) and `with_language()`.
* `PaddleOCREngine` — Protocol for the recognition call.
* `DefaultPaddleEngine` — default engine backed by the ``paddleocr``
  library, **imported lazily** so the module loads without the dependency.
* `PaddleOCRResultMapper` — converts PaddleOCR's per-word output
  (text + confidence in [0,1]) into the normalised `OCRResult`, grouping
  words per page and filtering by `drop_score`.
* `PaddleOCRProvider` — implements `OCRProvider`; all PaddleOCR specifics
  are confined here and made testable via an injected `PaddleOCREngine`.

## Plugin (`lexmind/ocr/providers/paddle_plugin.py`)

```python
plugin = PaddleOCRPlugin(
    dispatcher,
    config=PaddleOCRConfig(language="ro"),
    engine=my_engine,        # optional override
)
plugin.start()               # registers "paddleocr" into the dispatcher
```

`PaddleOCRPlugin` extends `OCRProviderPlugin` (Task 32), so it inherits the
registration wiring and declares `PluginCapability.OCR`; default plugin id is
`paddleocr` and the active config is exposed via `.paddle_config`.

## Design notes

* **Engine parity**: the PaddleOCR and Tesseract providers share the same
  shape (config + engine Protocol + mapper + provider), so adding another
  engine is purely additive.
* **Testability**: the provider and plugin are unit-tested with a stub
  engine; only `DefaultPaddleEngine` (requires the native ``paddleocr``
  dependency) is outside unit coverage by design.
* **Framework-only core**: the config, mapper, provider and plugin contain
  no infrastructure imports; the native binding is lazily imported.
