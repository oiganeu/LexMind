# OCR Pipeline - Acceptance Criteria (Task 44)

## AC-1: Value objects
- [x] `PipelineStepResult` carries `step_name`, `data`, `metadata`, `duration_ms`.
- [x] `OcrPipelineOptions` carries an ordered `step_names` list and exposes
      `enabled(name)` / `keeps(step_name)`.
- [x] `OcrPipelineResult` carries `page_number`, `step_results`, `final_text`,
      `duration_ms`, `is_success` and reports `step_count`.

## AC-2: Step contract and registry
- [x] `OcrPipelineStep` is a `runtime_checkable` Protocol (`name`, `process`).
- [x] `PipelineContext` is a frozen dataclass carrying `image_data` and a
      shared `state` dict.
- [x] `IdentityPipelineStep` records the input (no external dependency).
- [x] `OcrPipelineStepRegistry.register` rejects empty names; `get` raises
      `OcrPipelineStepNotFoundError` for unknown names; `has` /
      `registered_names` reflect state.

## AC-3: Service orchestration
- [x] `OcrPipelineService.run` resolves ordered steps (from options or the
      configured default) and accumulates `PipelineStepResult`s.
- [x] `OcrPipelineStarted` / `OcrPipelineStepCompleted` / `OcrPipelineCompleted`
      are emitted; on failure `OcrPipelineFailed` is emitted, the run stops and
      the error propagates.
- [x] A requested step that is not registered raises
      `OcrPipelineStepNotFoundError`.

## AC-4: Plugin integration
- [x] `OcrPipelinePlugin` declares `PluginCapability.OCR_PIPELINE`.
- [x] By default it ships an `IdentityPipelineStep` and exposes `run` /
      `register_step`; `start` / `stop` transition state.

## AC-5: Quality gates
- [x] Code is ASCII-only and passes `ruff`.
- [x] Covered by `tests/unit/test_ocr_pipeline.py` (types, options, context,
      identity step, registry, service, events, plugin).
