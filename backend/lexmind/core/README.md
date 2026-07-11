# Core

## Purpose

The Core package is the LexMind platform kernel. It coordinates modules, loads
plugins, manages configuration, dispatches events, and exposes shared
interfaces used by every component.

The Core is technology-independent: it depends only on the Python standard
library and `typing`. It does **not** import FastAPI, SQLAlchemy, FAISS,
SQLite, Ollama, OpenAI, Qdrant, Redis, or any OCR/AI library.

## Architecture

```
bootstrap ──> Kernel ──> ModuleRegistry ──> Module*
                        └──> ServiceLocator
```

- **Kernel** — top-level coordinator (register, initialize, start, stop, health).
- **ModuleRegistry** — stores modules by id; rejects duplicate ids.
- **ServiceLocator** — exposes shared services by name.
- **BaseModule** — skeleton implementing the `Module` protocol.
- **Bootstrap** — orchestrates the startup workflow.

## Lifecycle

Modules transition through: `created → loaded → initialized → started →
paused → stopping → stopped`. `failed` and `unknown` are terminal/error
states. See `lifecycle.py`.

## Responsibilities

- Discover, register, initialize, start, stop modules.
- Expose shared services and configuration.
- Expose application metadata and capability registry.
- Run health checks.

The Kernel does **not** execute business logic.

## Design Principles

- Dependency inversion: everything depends on `interfaces.py` protocols.
- Strongly typed capabilities and health via enums/dataclasses.
- No external technology locks.

## Interfaces

`interfaces.py` defines protocols for `Module`, `Kernel`, `Registry`,
`HealthProvider`, `CapabilityProvider`, `ConfigurationProvider`.
