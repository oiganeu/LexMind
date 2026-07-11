# Document Processing Pipeline

Orchestration framework that transforms imported documents into structured
knowledge. This package defines **only** the pipeline architecture — stage
declarations, execution, checkpointing, retries, metrics, and events. No
OCR, parsing, embeddings, or indexing logic lives here; those arrive later
as stage implementations.

## Architecture

```
PipelineManager
  ├── PipelineRegistry      registered stages + dependency graph
  ├── PipelineExecutor      sequential execution, retries, checkpoints
  │     └── CheckpointStore  save / restore / resume / reset
  └── EventBus (optional)   publishes lifecycle events
```

A `Pipeline` is an ordered selection of registered stages. A
`PipelineContext` carries the injected collaborators (workspace, document,
configuration, logger, kernel, event bus, plugin manager, statistics,
cancellation token) for a single run.

## Stages

Canonical order (`PIPELINE_STAGE_ORDER`):

1. Document Validation
2. Metadata Extraction
3. OCR
4. Language Detection
5. Document Classification
6. Parser
7. Entity Extraction
8. Chunking
9. Embeddings
10. Indexing
11. Knowledge Graph
12. Timeline
13. Contradiction Detection
14. Search Registration
15. Completed

Each stage exposes `id`, `name`, `description`, `version`, `enabled`,
`dependencies`, `estimated_duration_seconds`, `retry_policy`,
`timeout_seconds`, `health()`, `validate()`, `execute()`, and `rollback()`.
`BaseStage` provides defaults; its `execute()` raises
`NotImplementedYetError` until a concrete stage supplies behavior.

## Execution Flow

1. `pipeline.validate()` checks the dependency graph.
2. Statistics start; the initial (or restored) checkpoint is loaded.
3. For each stage in order:
   - already-completed stages (from a checkpoint) are skipped;
   - cancellation is checked before running;
   - `validate()` gates conditional / disabled stages;
   - `execute()` runs under the retry policy;
   - on success a checkpoint is created; on failure `rollback()` runs and
     the pipeline stops without corrupting prior stages.

## Stage Lifecycle

`PENDING → RUNNING → COMPLETED | FAILED | SKIPPED | ROLLED_BACK`

## Retry Policy

`RetryStrategy`: `NEVER`, `IMMEDIATE`, `FIXED_DELAY`, `EXPONENTIAL_BACKOFF`,
`CUSTOM`. `RetryPolicy.should_retry(attempt)` and `delay_for(attempt)`
drive the executor's retry loop.

## Checkpoint System

Every stage completion produces an immutable `Checkpoint` (completed
stages + shared state). `CheckpointStore` supports `save`, `restore`,
`resume`, and `reset`. Resuming re-hydrates `context.shared` and skips
completed stages. An `InMemoryCheckpointStore` is provided.

## Metrics

`PipelineStatistics` tracks start/end time, files processed, skipped
stages, and per-stage `StageMetrics` (start/end, CPU time, memory,
retries, failures, duration).

## Events

`PipelineStarted`, `StageStarted`, `StageCompleted`, `StageFailed`,
`CheckpointCreated`, `PipelineCompleted`, `PipelineCancelled`,
`PipelineFailed` — published through the injected `EventBus`.

## Future Parallelization

The executor runs sequentially today. The registry already computes a
topological order, enabling future parallel execution of independent
stages and distributed workers without changing the stage contract.
