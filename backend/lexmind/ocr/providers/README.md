# OCR Provider Interface (Task 32)

The **OCR Provider Interface** is the contract that lets new OCR engines be
plugged into LexMind without touching the orchestration layer. It consists
of two parts:

1. the `OCRProvider` Protocol — what every engine must implement; and
2. the `OCRDispatcher` — the registry/selector that resolves a provider at
   runtime.

This module additionally provides `OCRProviderPlugin`, which turns a
provider into a first-class plugin that registers itself with the shared
dispatcher on start and unregisters on stop.

## The contract: `OCRProvider`

```python
@runtime_checkable
class OCRProvider(Protocol):
    @property
    def name(self) -> str: ...
    def supports(self, mime_type: str) -> bool: ...
    def recognize(self, image_data: bytes, language: str = "",
                  mime_type: str = "") -> OCRResult: ...
```

* `name` — unique provider identifier (e.g. ``tesseract``).
* `supports` — declares which MIME types the engine can process.
* `recognize` — performs recognition and returns an engine-agnostic
  `OCRResult`.

Because it is a `runtime_checkable` Protocol, a provider needs no base
class and carries no framework dependency.

## Selection: `OCRDispatcher`

`OCRDispatcher` keeps a name → provider registry and resolves the right
provider via `select(name=..., mime_type=...)`:

1. explicit `name` if provided;
2. the configured `default_provider`;
3. the first registered provider whose `supports(mime_type)` is `True`.

Unknown names or unsupported MIME types raise `OCRProviderNotFoundError`.

## Plugin bridge: `OCRProviderPlugin`

```python
plugin = OCRProviderPlugin(dispatcher, TesseractOCRProvider())
plugin.start()   # registers the provider -> becomes the default
plugin.stop()    # unregisters the provider
```

* declares `PluginCapability.OCR`;
* exposes `.provider` and `.dispatcher`;
* registers the wrapped provider on `start()` and unregisters on `stop()`,
  keeping the dispatcher consistent with **no global state**.

## Implementing a new engine

To add a new OCR engine (e.g. PaddleOCR, a cloud API):

1. implement `OCRProvider` (`name`, `supports`, `recognize`) isolating all
   engine-specific code;
2. optionally wrap it in an `OCRResultMapper` if the engine emits
   per-word data;
3. package it as an `OCRProviderPlugin` and register it with the shared
   `OCRDispatcher`.

The `OCRPipeline` then discovers and uses it automatically — no changes to
the orchestration layer are required.
