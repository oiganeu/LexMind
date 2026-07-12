# Image Preprocessing (Task 36)

The **Image Preprocessing** framework prepares images for OCR through a
composable, engine-agnostic pipeline. It defines *what* to do declaratively
(`PreprocessingOptions`) and *how* via an injectable imaging engine, so the
framework, operations and pipeline contain no imaging-library imports and
are fully unit-testable with a stub engine.

## Architecture

```
PreprocessingOptions   -> declarative request (grayscale / deskew / denoise /
   |                       binarize / resize, or an explicit operation order)
   v
ImagePreprocessingPipeline
   |  resolves an ordered operation list
   v
ImageOperationRegistry -> name -> ImageOperation
   |                        (each delegates pixel work to ...)
   v
ImageEngine (Protocol) -> load / save / grayscale / binarize / resize /
                          deskew / denoise
   |
PillowImageEngine (default, lazy PIL import)  OR  a stub in tests
```

## Components (`lexmind/ocr/preprocessing/`)

* `preprocessing_types` -> `PreprocessingOptions` (validated, frozen) and
  `PreprocessingResult` (output bytes + applied operations).
* `image_engine` -> `ImageEngine` Protocol; the only place pixel work is
  defined. `PillowImageEngine` implements it with Pillow, imported lazily.
* `image_operation` -> `ImageOperation` base + `GrayscaleOperation`,
  `BinarizeOperation`, `ResizeOperation`, `DeskewOperation`,
  `DenoiseOperation`, plus `ImageOperationRegistry` and
  `build_default_registry`.
* `image_preprocessor` -> `ImagePreprocessor` Protocol and
  `ImagePreprocessingPipeline`, which resolves the operation order from the
  options, runs each step, emits lifecycle events and wraps failures in
  `ImageOperationError`.
* `preprocessing_events` -> `ImagePreprocessingStarted`,
  `ImagePreprocessingCompleted`, `ImagePreprocessingFailed`.
* `preprocessing_plugin` -> `ImagePreprocessingPlugin` declaring
  `PluginCapability.IMAGE_PREPROCESSING`.

## Usage

```python
engine = PillowImageEngine()
plugin = ImagePreprocessingPlugin(engine)
result = plugin.process(
    image_bytes,
    PreprocessingOptions(grayscale=True, deskew=True, binarize=True),
)
# result.applied_operations == ("grayscale", "deskew", "binarize")
```

An explicit order can be forced via `enabled_operations`, bypassing the
flag-based resolution.

## Design notes

* **Engine isolation**: all imaging libraries live behind `ImageEngine`; the
  framework depends only on the Protocol.
* **Composable & declarative**: operations are named, registered and ordered
  without code changes to the pipeline.
* **Testability**: the entire framework is unit-tested with a stub engine;
  only `PillowImageEngine` (requires the optional ``Pillow`` dependency) is
  outside unit coverage by design.
* **No global state / singletons**: engine, registry and event bus are
  injected.
