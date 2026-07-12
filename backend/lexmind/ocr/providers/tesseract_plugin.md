# Tesseract Plugin (Task 33)

The **Tesseract Plugin** is the concrete, ready-to-use packaging of the
Tesseract OCR engine as a LexMind plugin. It builds a
`TesseractOCRProvider` and registers it with a shared `OCRDispatcher` on
start, so the OCR pipeline can use Tesseract without any wiring code at the
call site.

## Implementation

`TesseractPlugin` lives in `lexmind/ocr/providers/tesseract_plugin.py` and
extends `OCRProviderPlugin` (Task 32). All provider-registration behaviour
is inherited; only engine construction is Tesseract-specific:

```python
plugin = TesseractPlugin(
    dispatcher,
    config=TesseractConfig(language="ron", psm=6),
    engine=my_engine,          # optional override (defaults to PytesseractEngine)
)
plugin.start()                 # registers "tesseract" into the dispatcher
```

* declares `PluginCapability.OCR`;
* default plugin id is `tesseract-ocr`;
* exposes `.tesseract_config` for inspection/configuration;
* `start()` registers the provider, `stop()` unregisters it (no global
  state).

## Engine composition

`TesseractOCRProvider` (Task 31) isolates all Tesseract-specific code:

* `TesseractConfig` — validated, frozen configuration (language, psm, oem,
  timeout, min_confidence) with `to_config_string` / `with_language`.
* `TesseractEngine` — Protocol for the recognition call.
* `PytesseractEngine` — default binding to `pytesseract` + `Pillow`,
  **imported lazily** so the module loads without the native binary.
* `OCRResultMapper` — converts Tesseract's per-word output into the
  engine-agnostic `OCRResult`.

Because the engine is injected behind `TesseractEngine`, the plugin (and
provider) are fully testable with a stub engine — no Tesseract binary or
`pytesseract` dependency required for unit tests.

## Usage

A host application composes a dispatcher, instantiates this plugin (and any
other OCR provider plugins) and starts them. The `OCRPipeline` then selects
Tesseract by name or MIME support automatically.
