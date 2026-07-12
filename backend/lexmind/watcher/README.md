# File Watcher

> Task 26 - Design the framework for a File Watcher.

The File Watcher monitors configured directories and emits file events
(create / modify / delete) while remaining independent of any
platform-specific change-notification mechanism.

## Responsibilities

- Monitor configured directories
- Emit file events
- Debounce rapid changes
- Filter supported file types
- Provide pluggable backends

## Components

| Component | Type | Role |
|-----------|------|------|
| `FileEvent` | domain event | Immutable record of a file change |
| `WatchBackend` | Protocol | Pluggable source of raw change notifications |
| `EventDispatcher` | Protocol | Delivers `FileEvent` instances downstream |
| `FileWatcher` | Protocol | Public orchestration contract |
| `FileWatcherService` | implementation | Filtering + debounce + dispatch |
| `InMemoryWatchBackend` | implementation | Programmatic / test backend |
| `StoragePollingBackend` | implementation | Storage-abstraction polling backend |
| `EventBusDispatcher` | implementation | Forwards events to the EventBus |
| `FileWatcherPlugin` | plugin | Registers the service with the plugin framework |

## Dependency flow

```
FileWatcher --> EventDispatcher
WatchBackend --> FileWatcher
```

`FileWatcherService` depends only on the `WatchBackend` and
`EventDispatcher` Protocols.  Concrete backends (`InMemoryWatchBackend`,
`StoragePollingBackend`) and concrete dispatchers (`EventBusDispatcher`)
are injected, so the orchestration logic is fully backend-independent.

## Behaviour

1. A `WatchConfig` is registered and started; the watcher asks its
   backend to observe `root_uri`.
2. Each raw backend notification is dropped unless its file extension
   matches `WatchConfig.patterns` (an empty filter accepts everything).
3. Matching notifications for the same URI are coalesced: only the
   latest one is emitted, and only after `debounce_seconds` of quiet
   time (trailing debounce).  A `debounce_seconds` of `0` emits
   immediately.
4. The resulting `FileEvent` is handed to the `EventDispatcher`, which
   normally publishes it on the EventBus.

## Usage

```python
from lexmind.watcher import (
    FileWatcherService,
    InMemoryWatchBackend,
    EventBusDispatcher,
    WatchConfig,
    FileEventType,
)

backend = InMemoryWatchBackend()
dispatcher = EventBusDispatcher(event_bus)
watcher = FileWatcherService(backend, dispatcher)

watcher.register(WatchConfig(
    watch_id="inbox",
    workspace_id="ws-1",
    root_uri="storage://ws-1/inbox",
    patterns={".pdf", ".png"},
    recursive=True,
    debounce_seconds=1.0,
))
watcher.start("inbox")

# ... backend.emit(BackendFileEvent(...)) in production ...
```

See `lexmind/watcher/acceptance.md` for the acceptance criteria and
`tests/unit/test_file_watcher.py` for the behavioural contract.
