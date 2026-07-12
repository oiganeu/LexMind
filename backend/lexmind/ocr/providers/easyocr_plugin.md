# EasyOCR Plugin (Task 35)

The **EasyOCR Plugin** adds EasyOCR — a popular, multi-language OCR engine
supporting 80+ languages — as a LexMind OCR provider. Like the Tesseract
(Task 33) and PaddleOCR (Task 34) plugins, it isolates all engine-specific
code behind the `OCRProvider` contract and is packaged as a plugin that
registers with a shared `OCRDispatcher`.

## Components (`lexmind/ocr/providers/easyocr_provider.py`)

* `EasyOCRConfig` — frozen, validated config (`languages`, `gpu`,
  `detail`, `min_confidence`) with `to_kwargs()` (for the `easyocr.Reader`
  call) and `with_languages()`.
* `EasyOCREngine` — Protocol for the recognition call.
* `DefaultEasyEngine` — default engine backed by the ``easyocr`` library,
  **imported lazily** so the module loads without the dependency.
* `EasyOCRResultMapper` — converts EasyOCR's per-word output (text +
  confidence in [0,1]) into the normalised `OCRResult`, grouping words per
  page and filtering by `min_confidence`.
* `EasyOCRProvider` — implements `OCRProvider`; all EasyOCR specifics are
  confined here and made testable via an injected `EasyOCREngine`.

## Plugin (`lexmind/ocr/providers/easyocr_plugin.py`)

```python
plugin = EasyOCRPlugin(
    dispatcher,
    config=EasyOCRConfig(languages=("ro", "en")),
    engine=my_engine,        # optional override
)
plugin.start()               # registers "easyocr" into the dispatcher
```

`EasyOCRPlugin` extends `OCRProviderPlugin` (Task 32), so it inherits the
registration wiring and declares `PluginCapability.OCR`; default plugin id is
`easyocr` and the active config is exposed via `.easy_config`.

## Design notes

* **Engine parity**: Tesseract, PaddleOCR and EasyOCR providers share the
  same shape (config + engine Protocol + mapper + provider), so adding
  another engine is purely additive.
* **Testability**: the provider and plugin are unit-tested with a stub
  engine; only `DefaultEasyEngine` (requires the native ``easyocr``
  dependency) is outside unit coverage by design.
* **Framework-only core**: the config, mapper, provider and plugin contain
  no infrastructure imports; the native binding is lazily imported.
