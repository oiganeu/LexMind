# OCR Provider Interface - Acceptance Criteria (Task 32)

## AC-1: Provider contract
- [x] `OCRProvider` is a `runtime_checkable` Protocol with `name`,
      `supports(mime_type)` and `recognize(image_data, language, mime_type)
      -> OCRResult`.
- [x] The contract carries no framework / infrastructure dependency.

## AC-2: Provider selection
- [x] `OCRDispatcher.register` adds a provider and assigns a default.
- [x] `select` resolves by explicit name, then default, then MIME support.
- [x] Unknown name / unsupported MIME raises `OCRProviderNotFoundError`.
- [x] `unregister` keeps the default consistent.

## AC-3: Plugin integration
- [x] `OCRProviderPlugin` declares `PluginCapability.OCR`.
- [x] It wraps an `OCRProvider` plus a shared `OCRDispatcher`.
- [x] `start()` registers the provider (and makes it the default);
      `stop()` unregisters it.
- [x] `.provider` and `.dispatcher` are exposed.
- [x] `None` dispatcher or `None` provider is rejected.

## AC-4: Extension model
- [x] A new engine only needs to implement `OCRProvider`; no orchestration
      change is required for the pipeline to discover it.
- [x] The plugin bridge avoids global state (registration is per-dispatcher
      via dependency injection).

## AC-5: Quality gates
- [x] Code is ASCII-only and passes `ruff`.
- [x] The plugin is covered by `tests/unit/test_ocr_provider_plugin.py`.
