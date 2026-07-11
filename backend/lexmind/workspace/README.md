# LexMind Workspace Engine

The Workspace Engine manages the creation, lifecycle, isolation, and migration of independent workspaces. Every document, index, graph, cache, report, and configuration belongs to exactly one workspace.

No OCR. No AI. No database implementation. No indexing. Only the workspace framework.

---

## Workspace Layout

Each workspace has a standard directory structure:

```
workspace/
  workspace.yaml       # Manifest (authoritative config)
  metadata/
  original/
  processed/
  extracted/
  cache/
  indexes/
  graph/
  reports/
  exports/
  logs/
  plugins/
  temp/
```

---

## Lifecycle States

```
CREATED -> OPEN -> ACTIVE -> LOCKED -> ACTIVE
                   |          |
                   v          v
               READ_ONLY    CLOSED -> ARCHIVED
                              ^          |
                              |          v
                              +--- OPEN -+
```

Terminal state: `CORRUPTED` (no outgoing transitions).

---

## Manifest

The manifest (`workspace.yaml`) stores:

| Field | Description |
|---|---|
| `version` | Manifest schema version (currently `1.0.0`) |
| `workspace_id` | Unique workspace identifier |
| `name` | Human-readable name |
| `description` | Optional description |
| `created_at` | UTC creation timestamp |
| `language` | Default language (e.g. `ro`) |
| `default_plugins` | List of plugin names |
| `enabled_features` | Feature flags |
| `storage_version` | Storage format version |

Validation is performed by `ManifestValidator`.

---

## Architecture

| Component | Description |
|---|---|
| `Workspace` | Aggregate root with lifecycle methods |
| `WorkspaceManager` | Orchestrates create/open/close/archive/delete |
| `WorkspaceFactory` | Protocol for creating new workspaces |
| `WorkspaceLoader` | Protocol for loading existing workspaces |
| `WorkspaceRegistry` | Protocol for tracking open instances |
| `WorkspaceLock` | Protocol for concurrency control |
| `WorkspaceManifest` | Immutable manifest value object |
| `WorkspaceMetadata` | Immutable metadata value object |
| `WorkspaceContext` | Runtime dependency interfaces |

---

## Locking

Three strategies are supported via the `WorkspaceLock` protocol:

1. **SingleProcessLock** -- in-process threading lock (default)
2. **Multi-process lock** -- future: file-based or Redis
3. **Distributed lock** -- future: Redlock / etcd

---

## Migration

Migration is defined by `from_version` and `to_version` fields on the `WorkspaceMigrated` event. The `WorkspaceManager.migrate_workspace()` method orchestrates version bumps. Actual migration logic is not yet implemented.

---

## Isolation Model

Each workspace is fully isolated:
- Separate directory tree
- Separate manifest and configuration
- Separate index, graph, and cache stores
- No shared state between workspaces

The `WorkspaceRegistry` tracks which workspaces are currently open in the process.

---

## Testing

```bash
uv run python -m pytest tests/unit/test_workspace_engine.py -v
```
