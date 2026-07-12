# OCR Pipeline

The OCR pipeline runs an **ordered, composable sequence of processing steps**
over a single document page image and aggregates their results.  It mirrors the
architecture of `lexmind/table_detection/` but is self-contained: it defines its
own step `Protocol` and never reaches into the implementation details of other
packages.

## Concepts

- **Pipeline steps** implement `OcrPipelineStep` (`name`, `process(context) ->
  PipelineStepResult`).  A `PipelineContext` carries the raw `image_data` plus a
  shared mutable `state` dict so later steps can build on earlier ones.
- **Registry** (`OcrPipelineStepRegistry`) maps step names to implementations;
  `IdentityPipelineStep` is a dependency-free passthrough shipped by default.
- **Service** (`OcrPipelineService`) resolves the ordered step sequence (from
  `OcrPipelineOptions` or a configured default), runs each enabled step,
  accumulates `PipelineStepResult`s and publishes lifecycle events.
- **Plugin** (`OcrPipelinePlugin`) declares `PluginCapability.OCR_PIPELINE`,
  ships a default sequence and exposes `run(...)` / `register_step(...)`.

## Events

`OcrPipelineStarted`, `OcrPipelineStepCompleted`, `OcrPipelineCompleted` and
`OcrPipelineFailed` are published on the injected `EventBus`.  A failing step
emits `OcrPipelineFailed` and stops the run (the original error is re-raised).

## Extending

Register a custom step under the plugin (or service) registry:

```python
plugin.register_step(MyCustomStep())
result = plugin.run(image_bytes, page_number=1)
```

Run only a subset of steps with `OcrPipelineOptions(step_names=(...))`.
