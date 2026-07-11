# Storage Abstraction Layer

Backend-agnostic file storage for LexMind.

## Architecture

```
Application / Workspace / Artifacts
          |
    StorageManager          (façade -- URI-based API)
          |
    StorageProvider         (Protocol -- path-based)
          |
    FilesystemStorageProvider  (concrete -- pathlib only)
```

## Quick Start

```python
from pathlib import Path
from lexmind.storage import StorageManager, FilesystemStorageProvider

provider = FilesystemStorageProvider(Path("/data/storage"))
manager = StorageManager(provider)

manager.save("storage://ws/docs/file.pdf", b"...")
data = manager.load("storage://ws/docs/file.pdf")
```

## URI Format

```
storage://<workspace>/<path>
```

Examples:
- `storage://main/documents/contract.pdf`
- `storage://main/artifacts/abc123/meta.json`

## StorageProvider Protocol

Every backend must implement:

| Method        | Description                          |
|---------------|--------------------------------------|
| `exists()`    | Check if object exists               |
| `read_bytes()`| Read raw bytes                       |
| `write_bytes()`| Write raw bytes                     |
| `read_text()` | Read decoded text                    |
| `write_text()`| Write text                           |
| `delete()`    | Delete object                        |
| `copy()`      | Copy object                          |
| `move()`      | Move object                          |
| `mkdir()`     | Create directory                     |
| `list()`      | List immediate children              |
| `walk()`      | Walk directory tree                  |
| `stat()`      | Get stat information                 |
| `checksum()`  | Compute checksum                     |
| `open()`      | Open file handle                     |
| `resolve()`   | Resolve to absolute backend path     |

## Constraints

- **No `os.path`** -- use `pathlib` exclusively.
- **No global state** -- all state lives in the provider instance.
- **Dependency injection** -- `StorageManager` receives the provider.
- **No path leakage** -- absolute paths never leave the provider.
