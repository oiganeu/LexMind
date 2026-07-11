"""Runtime context provided to every plugin."""

from dataclasses import dataclass, field
from typing import Any

from lexmind.core.kernel import Kernel
from lexmind.events.event_bus import EventBus


@dataclass
class PluginContext:
    """Services a plugin may use, injected at load time.

    No global state is used; everything a plugin needs is passed through
    this context object.
    """

    config: dict[str, Any] = field(default_factory=dict)
    logger: Any = None
    event_bus: EventBus | None = None
    kernel: Kernel | None = None
    service_provider: Any = None
    workspace: str | None = None
