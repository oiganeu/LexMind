# Image Preprocessing - Acceptance Criteria (Task 36)

## AC-1: Options and result model
- [x] `PreprocessingOptions` validates `binarize_threshold` ([0,1]) and
      `resize_max_dim` (>=0).
- [x] `is_empty` reports whether any preprocessing is requested.
- [x] `PreprocessingResult` records output bytes and applied operations;
      `was_modified` reflects whether anything ran.

## AC-2: Operations and registry
- [x] `GrayscaleOperation`, `BinarizeOperation`, `ResizeOperation`,
      `DeskewOperation`, `DenoiseOperation` each implement `ImageOperation`.
- [x] `ImageOperationRegistry.register` rejects empty names; `get` raises
      `ImageOperationError` for unknown names; `has` / `registered_names`
      reflect state.
- [x] `build_default_registry` yields the five standard operations.

## AC-3: Pipeline orchestration
- [x] `ImagePreprocessingPipeline.process` resolves the operation order from
      the options (flags or explicit `enabled_operations`).
- [x] An empty request returns the input unchanged (no operations applied).
- [x] Operations run in order; each applied operation is recorded.
- [x] `ImagePreprocessingStarted` / `ImagePreprocessingCompleted` are emitted;
      on failure `ImagePreprocessingFailed` is emitted and the error is
      wrapped in `ImageOperationError`.

## AC-4: Engine contract
- [x] `ImageEngine` is a Protocol with `load`/`save` and the five transforms.
- [x] `PillowImageEngine` implements it with Pillow, imported lazily so the
      framework is importable without the dependency.

## AC-5: Plugin integration
- [x] `ImagePreprocessingPlugin` declares `PluginCapability.IMAGE_PREPROCESSING`
      and exposes `process` / `pipeline`.
- [x] A `None` engine is rejected; `start` / `stop` transition state.

## AC-6: Quality gates
- [x] Pixel work is isolated behind `ImageEngine`; the framework has no
      imaging-library imports.
- [x] Code is ASCII-only and passes `ruff`.
- [x] Covered by `tests/unit/test_image_preprocessing.py` with a stub engine;
      only `PillowImageEngine` is outside unit coverage by design.
