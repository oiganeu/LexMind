# File Watcher - Acceptance Criteria

## Interfaces
- `FileEvent` (domain event) and `FileEventType` are defined.
- `WatchBackend` Protocol defines `watch`, `unwatch`, `is_watching`.
- `EventDispatcher` Protocol defines `dispatch`.
- `FileWatcher` Protocol defines `register`, `start`, `stop`,
  `is_watching`, `watching_ids`, `flush`.
- `FileWatcherService` implements `FileWatcher`.

## Behaviour
- A create notification emits exactly one `FileEvent` of type `CREATED`.
- A modify notification emits exactly one `FileEvent` of type `MODIFIED`.
- A delete notification emits exactly one `FileEvent` of type `DELETED`.
- Rapid successive changes to the same file are debounced into a single
  trailing event.
- Files whose extension is not in `WatchConfig.patterns` are ignored
  (empty patterns accept all).
- Disabled watches are ignored.
- Events are delivered through the injected `EventDispatcher`, never via
  a hard-coded sink.

## Abstraction / backend independence
- `FileWatcherService` depends only on the `WatchBackend` and
  `EventDispatcher` Protocols.
- At least two backends are provided (`InMemoryWatchBackend`,
  `StoragePollingBackend`) and both drive the same watcher logic.
- `StoragePollingBackend` accesses storage exclusively through
  `StorageManager` (no direct filesystem / OS API usage).

## Quality
- Unit tests cover watch create / modify / delete and debounce.
- Test coverage of `lexmind/watcher` is greater than 95%.
- Ruff and MyPy are clean.
