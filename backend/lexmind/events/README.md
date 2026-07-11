# Events

## Purpose

The Events package provides the event-driven messaging infrastructure of
LexMind. Modules publish and subscribe to events without direct knowledge
of each other, enabling loose coupling.

This package depends only on the Python standard library. No networking,
no database, no external dependencies.

## Architecture

```
EventBus
  ├── EventRegistry      (known event types)
  ├── SubscriptionRegistry (event_name -> handlers, priority ordered)
  └── EventDispatcher     (routing, error isolation, timing, hooks)
```

## Event Model

Every `Event` carries: `event_id`, `name`, `timestamp`, `correlation_id`,
`source_module`, `version`, `priority`, `payload`, `context`, `metadata`.

## Lifecycle

1. A module calls `EventBus.publish(event)`.
2. The bus resolves subscribers for `event.name`.
3. The dispatcher invokes each handler in priority order (HIGH → LOW).
4. Each handler error is isolated; remaining handlers still execute.
5. Results and timings update the bus statistics.

## Publishing

```python
from lexmind.events import Event, EventBus, EventType

bus = EventBus()
bus.publish(Event(name=EventType.MODULE_STARTED, source_module="core"))
```

## Subscription

```python
bus.subscribe_fn(
    EventType.MODULE_STARTED,
    lambda e: print("started", e.source_module),
    name="logger",
)
```

## Ordering

Handlers are invoked in descending `EventPriority` order. Within the same
priority, registration order is preserved.

## Error Isolation

A failing handler is recorded as `success=False` in its `EventResult` but
does **not** stop the bus. Subsequent handlers still run.

## Future Async Support

The dispatcher is synchronous today. Its interface is intentionally async
ready: an async dispatch path can replace the loop without changing the
bus API.

## Diagnostics

`EventBus.statistics` exposes published, dropped, handler invocations,
error count, and average handler duration.
