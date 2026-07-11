"""Event-driven messaging infrastructure for LexMind."""

from lexmind.events.event import Event
from lexmind.events.event_bus import EventBus
from lexmind.events.event_context import EventContext
from lexmind.events.event_exceptions import (
    DuplicateHandlerError,
    EventBusError,
    HandlerError,
    UnknownEventError,
)
from lexmind.events.event_handler import EventHandler, FunctionHandler
from lexmind.events.event_metadata import EventMetadata
from lexmind.events.event_priority import EventPriority
from lexmind.events.event_registry import EventRegistry
from lexmind.events.event_result import EventResult
from lexmind.events.event_types import EventType
from lexmind.events.subscriptions import Subscription, SubscriptionRegistry

__all__ = [
    "Event",
    "EventBus",
    "EventBusError",
    "EventContext",
    "DuplicateHandlerError",
    "EventHandler",
    "EventHandler",
    "EventMetadata",
    "EventPriority",
    "EventRegistry",
    "EventResult",
    "EventType",
    "FunctionHandler",
    "HandlerError",
    "Subscription",
    "SubscriptionRegistry",
    "UnknownEventError",
]
