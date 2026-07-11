"""Unit tests for the LexMind Event Bus."""

from lexmind.events import (
    Event,
    EventBus,
    EventPriority,
    EventType,
    FunctionHandler,
)
from lexmind.events.event_exceptions import DuplicateHandlerError


def _event(name: str = EventType.MODULE_STARTED) -> Event:
    return Event(name=name, source_module="test")


def test_publish_event() -> None:
    bus = EventBus()
    received: list[Event] = []
    bus.subscribe_fn(EventType.MODULE_STARTED, lambda e: received.append(e))
    bus.publish(_event())
    assert len(received) == 1
    assert bus.statistics.published == 1


def test_subscribe_handler() -> None:
    bus = EventBus()
    bus.subscribe_fn(EventType.MODULE_STOPPED, lambda e: None, name="h1")
    assert len(bus.handlers(EventType.MODULE_STOPPED)) == 1


def test_unsubscribe_handler() -> None:
    bus = EventBus()
    bus.subscribe_fn(EventType.MODULE_LOADED, lambda e: None, name="h1")
    bus.unsubscribe(EventType.MODULE_LOADED, "h1")
    assert bus.handlers(EventType.MODULE_LOADED) == []


def test_multiple_handlers() -> None:
    bus = EventBus()
    seen: list[str] = []

    def make(label: str) -> FunctionHandler:
        return bus.subscribe_fn(EventType.DOCUMENT_ADDED, lambda e: seen.append(label), name=label)

    make("a")
    make("b")
    bus.publish(_event(EventType.DOCUMENT_ADDED))
    assert seen == ["a", "b"]


def test_handler_ordering_by_priority() -> None:
    bus = EventBus()
    order: list[str] = []

    def make(label: str, prio: EventPriority) -> None:
        bus.subscribe_fn(
            EventType.HEALTH_CHANGED, lambda e: order.append(label), name=label, priority=prio
        )

    make("low", EventPriority.LOW)
    make("high", EventPriority.HIGH)
    make("normal", EventPriority.NORMAL)
    bus.publish(_event(EventType.HEALTH_CHANGED))
    assert order == ["high", "normal", "low"]


def test_unknown_event_dropped() -> None:
    bus = EventBus()
    bus.publish(_event("custom.unregistered.event"))
    assert bus.statistics.dropped == 1
    assert bus.statistics.published == 0


def test_duplicate_registration_rejected() -> None:
    bus = EventBus()
    bus.subscribe_fn(EventType.PLUGIN_LOADED, lambda e: None, name="dup")
    try:
        bus.subscribe_fn(EventType.PLUGIN_LOADED, lambda e: None, name="dup")
    except DuplicateHandlerError:
        pass
    else:
        raise AssertionError("expected DuplicateHandlerError")


def test_failure_isolation() -> None:
    bus = EventBus()
    seen: list[str] = []
    bus.subscribe_fn(
        EventType.MODULE_FAILED,
        lambda e: (_ for _ in ()).throw(RuntimeError("boom")),
        name="bad",
    )
    bus.subscribe_fn(EventType.MODULE_FAILED, lambda e: seen.append("ok"), name="good")
    results = bus.publish(_event(EventType.MODULE_FAILED))
    assert seen == ["ok"]
    assert any(not r.success for r in results)
    assert bus.statistics.errors == 1
