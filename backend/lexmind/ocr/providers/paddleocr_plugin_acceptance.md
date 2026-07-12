# PaddleOCR Plugin - Acceptance Criteria (Task 34)

## AC-1: Provider contract
- [x] `PaddleOCRProvider` implements `OCRProvider` (`name == "paddleocr"`,
      `supports`, `recognize`).
- [x] `recognize` rejects empty `image_data` and honours language overrides.

## AC-2: Configuration
- [x] `PaddleOCRConfig` validates `language`, `det_db_box_thresh` and
      `drop_score` (both in [0,1]).
- [x] `to_kwargs()` returns the paddleocr call arguments; `with_language`
      returns a copy when a different language is supplied.

## AC-3: Result mapping
- [x] `PaddleOCRResultMapper.to_result` groups words per page, computes the
      mean confidence (already normalised to [0,1]) and drops words below
      `min_confidence`.
- [x] The produced `OCRResult` carries `provider == "paddleocr"`, language
      and per-page results.

## AC-4: Plugin integration
- [x] `PaddleOCRPlugin` extends `OCRProviderPlugin`, declares
      `PluginCapability.OCR` and defaults its id to `paddleocr`.
- [x] `start()` registers the `paddleocr` provider; `stop()` unregisters it.
- [x] `.paddle_config` exposes the active configuration.
- [x] A `None` dispatcher is rejected.

## AC-5: Quality gates
- [x] Engine specifics are isolated; the orchestration layer depends only on
      the `OCRProvider` contract.
- [x] Code is ASCII-only and passes `ruff`.
- [x] Covered by `tests/unit/test_paddleocr_plugin.py` (config, mapper,
      provider, plugin) with a stub engine; the native `DefaultPaddleEngine`
      is excluded from unit coverage by design.
