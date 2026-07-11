# LexMind Backend

Python backend for the LexMind legal intelligence platform.

## Stack

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) — package manager
- FastAPI — web framework
- Uvicorn — ASGI server
- Pydantic v2 — validation
- pydantic-settings — configuration
- structlog — structured logging

## Install

```bash
uv sync
```

## Run

```bash
uv run uvicorn lexmind.main:app --reload
```

Health endpoint: `GET /` returns `{"name": "LexMind", "status": "ok", "version": "..."}`.

## Test

```bash
uv run pytest
```

## Lint

```bash
uv run ruff check
```

## Format

```bash
uv run black .
```

## Type check

```bash
uv run mypy
```

## Structure

```
lexmind/
    api/          HTTP routes and middleware
    core/         Bootstrap, settings, logging, lifecycle
    domain/       Entities and domain services
    infrastructure/ External adapters and persistence
    application/  Use cases and orchestration
    shared/       Common utilities and types
    plugins/      Plugin interface and loader
    services/     Business services
    workers/      Background task workers
    events/       Event emission and handling
    interfaces/   Port definitions
    utils/        Helper functions
```
