# Document Ingestion Engine

The ingestion framework imports files into LexMind. It discovers files,
identifies formats, tracks import jobs, detects duplicates, extracts basic
metadata, and dispatches the next processing stage via events.

This package is framework-only: it performs **no** OCR, parsing,
embedding, indexing, or AI.

## Architecture

- `IngestionManager` — entry point; creates jobs, wires collaborators,
  runs the pipeline, measures duration, publishes events, cancels jobs.
- `IngestionRegistry` — registers sources by name and tracks jobs.
- `IngestionSource` (Protocol) — the contract every source implements.
  Only `FileDiscovery` (filesystem) is implemented; S3, WebDAV,
  SharePoint, Google Drive, Nextcloud, and network shares are future.
- `IngestionPipeline` — runs the framework stages.
- `IngestionContext` — per-job injected collaborators and shared state.
- `IngestionJob` / `JobState` — job model and validated state machine.
- `IngestionSession` — groups jobs for resumable, multi-source imports.

## Pipeline

```
Discover -> Validate -> Identify Type -> Calculate Checksum ->
Register (duplicate check) -> Publish Events -> Ready for OCR
```

Files passing all stages are marked `IMPORTED` and are ready to be handed
to the next processing stage (OCR), which is out of scope here.

## Job States

`CREATED -> DISCOVERING -> VALIDATING -> IMPORTING -> COMPLETED`, with
`PAUSED`, `CANCELLED`, and `FAILED` transitions. Transitions are validated
by `can_transition`; invalid transitions raise `InvalidJobStateError`.

## Supported File Types

Documents (PDF, DOCX, ODT, TXT, RTF, HTML), email (EML, MSG), and images
(PNG, JPEG, TIFF, BMP, WEBP) are supported now. Audio, video, and archives
are recognized but reserved for future implementation.

## Duplicate Detection

`DuplicateDetector` tracks SHA-256 checksums per run. A persistent,
cross-session store backed by a repository is a future extension.

## Events

`ingestion.import_started`, `ingestion.import_progress`,
`ingestion.file_discovered`, `ingestion.file_validated`,
`ingestion.file_rejected`, `ingestion.duplicate_detected`,
`ingestion.import_completed`, `ingestion.import_failed`.

## Error Handling

Per-file failures are recorded as `FileResult` outcomes
(`REJECTED`, `UNSUPPORTED`, `ERROR`) without aborting the job. Fatal
errors transition the job to `FAILED` and raise `IngestionError`.

## Statistics

`IngestionStatistics` tracks total, imported, skipped, duplicates,
unsupported, errors, duration, and average file time.

## Future Extensions

Watched folders, drag & drop, ZIP archives, resumable imports across
sessions, content-based MIME sniffing, and remote sources.

## Example

```python
manager = IngestionManager(event_bus=bus)
job = manager.create_job(workspace_id="ws1", source="filesystem", location="/docs")
result = manager.run(job, location="/docs")
```
