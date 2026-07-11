# TASK-0010

## Title

Implement the Document Ingestion Engine Framework

---

## Goal

Design the document ingestion pipeline that imports files into LexMind.

The ingestion engine is responsible for discovering documents,
identifying formats,
tracking import jobs,
detecting duplicates,
extracting metadata,
and dispatching the next processing stages.

This task creates only the framework.

No OCR.

No parsing.

No embeddings.

No indexing.

No AI.

---

# Objectives

The ingestion engine must support

- recursive folder import
- drag & drop import (future)
- ZIP archives (future)
- watched folders (future)
- duplicate detection
- metadata extraction
- import sessions
- resumable imports
- progress tracking
- cancellation
- validation
- event publishing

---

# Create Directory Structure

backend/lexmind/ingestion/

    README.md

    __init__.py

    ingestion_manager.py

    ingestion_job.py

    ingestion_session.py

    ingestion_pipeline.py

    ingestion_context.py

    ingestion_result.py

    ingestion_registry.py

    ingestion_statistics.py

    ingestion_events.py

    ingestion_exceptions.py

    file_discovery.py

    duplicate_detector.py

    mime_detector.py

    checksum.py

    path_validator.py

---

# Supported Sources

Design interfaces for

Filesystem

Workspace

Future

S3

WebDAV

SharePoint

Google Drive

Nextcloud

Network Shares

---

# Supported File Types

PDF

DOCX

ODT

TXT

RTF

HTML

EML

MSG

PNG

JPEG

TIFF

BMP

WEBP

MP3 (future)

WAV (future)

MP4 (future)

MKV (future)

ZIP (future)

---

# Import Job

Every import job must contain

Job ID

Workspace ID

Status

Start Time

End Time

Progress

Source

Files Processed

Files Failed

Warnings

Statistics

---

# Job States

Enum

CREATED

DISCOVERING

VALIDATING

IMPORTING

PAUSED

CANCELLED

COMPLETED

FAILED

---

# Duplicate Detection

Design interfaces for

SHA-256 checksum

File size

Filename

Future content similarity

No implementation.

---

# MIME Detection

Use MIME type.

Never rely only on extension.

Design provider interface.

---

# Path Validation

Reject

Broken symlinks

Invalid filenames

Hidden system files (configurable)

Permission denied

Unsupported files

---

# Import Pipeline

Pipeline skeleton

Discover Files

↓

Validate

↓

Identify Type

↓

Calculate Checksum

↓

Register Job

↓

Publish Events

↓

Ready for OCR

No OCR implementation.

---

# Events

Define

ImportStarted

ImportProgress

FileDiscovered

FileValidated

FileRejected

DuplicateDetected

ImportCompleted

ImportFailed

---

# Statistics

Track

Total files

Imported

Skipped

Duplicates

Unsupported

Errors

Duration

Average file time

---

# Documentation

Create

backend/lexmind/ingestion/README.md

Explain

Architecture

Pipeline

Future extensions

Error handling

Statistics

---

# Unit Tests

Verify

Job creation

State transitions

Discovery

Validation

Duplicate detection interface

Statistics

Pipeline creation

---

# Acceptance Criteria

Framework compiles.

Interfaces complete.

No OCR.

No parsing.

No indexing.

Events defined.

Statistics model exists.

---

# Estimated Time

5 hours

---

# Priority

Critical

---

# Dependencies

TASK-0006

TASK-0007

TASK-0008

TASK-0009
