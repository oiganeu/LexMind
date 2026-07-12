# EasyOCR Plugin - Acceptance Criteria (Task 35)

## AC-1: Provider contract
- [x] `EasyOCRProvider` implements `OCRProvider` (`name == "easyocr"`,
      `supports`, `recognize`).
- [x] `recognize` rejects empty `image_data` and honours language overrides
      (single language translates to a one-element tuple).

## AC-2: Configuration
- [x] `EasyOCRConfig` validates `languages` (non-empty), `detail` (0/1) and
      `min_confidence` (in [0,1]).
- [x] `to_kwargs()` returns the `easyocr.Reader` arguments;
      `with_languages` returns a copy when different languages are supplied.

## AC-3: Result mapping
- [x] `EasyOCRResultMapper.to_result` groups words per page, computes the
      mean confidence (already normalised to [0,1]) and drops words below
      `min_confidence`.
- [x] The produced `OCRResult` carries `provider == "easyocr"`, the first
      language and per-page results.

## AC-4: Plugin integration
- [x] `EasyOCRPlugin` extends `OCRProviderPlugin`, declares
      `PluginCapability.OCR` and defaults its id to `easyocr`.
- [x] `start()` registers the `easyocr` provider; `stop()` unregisters it.
- [x] `.easy_config` exposes the active configuration.
- [x] A `None` dispatcher is rejected.

## AC-5: Quality gates
- [x] Engine specifics are isolated; the orchestration layer depends only on
      the `OCRProvider` contract.
- [x] Code is ASCII-only and passes `ruff`.
- [x] Covered by `tests/unit/test_easyocr_plugin.py` (config, mapper,
      provider, plugin) with a stub engine; the native `DefaultEasyEngine`
      is excluded from unit coverage by design.
