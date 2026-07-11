"""LexMind Core Kernel.

The kernel coordinates module discovery, registration, initialization,
start, stop, and health checks. It does not execute business logic.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from lexmind.core.health import Health, HealthStatus
from lexmind.core.interfaces import Module
from lexmind.core.lifecycle import LifecycleState
from lexmind.core.registry import DuplicateModuleError, ModuleNotFoundError, ModuleRegistry
from lexmind.core.service_locator import ServiceLocator
from lexmind.exceptions import LexMindError


class KernelError(LexMindError):
    """Raised for kernel-level failures."""


@dataclass
class Kernel:
    """Central coordinator of LexMind modules."""

    name: str = "LexMind Kernel"
    registry: ModuleRegistry = field(default_factory=ModuleRegistry)
    services: ServiceLocator = field(default_factory=ServiceLocator)
    capabilities: dict[str, Module] = field(default_factory=dict)

    def register_module(self, module: Module) -> None:
        self.registry.register(module)
        for capability in module.capabilities:
            self.capabilities[capability.value] = module

    def unregister_module(self, module_id: str) -> None:
        module = self.registry.get(module_id)
        for capability in module.capabilities:
            self.capabilities.pop(capability.value, None)
        self.registry.unregister(module_id)

    def initialize_modules(self) -> None:
        for module in self.registry.list():
            module.initialize()

    def start_modules(self) -> None:
        for module in self.registry.list():
            module.start()

    def stop_modules(self) -> None:
        for module in self.registry.list():
            module.stop()

    def health(self) -> HealthStatus:
        if not self.registry.list():
            return HealthStatus.UNKNOWN
        statuses = {m.health().status for m in self.registry.list()}
        if statuses == {HealthStatus.HEALTHY}:
            return HealthStatus.HEALTHY
        if HealthStatus.UNAVAILABLE in statuses:
            return HealthStatus.UNAVAILABLE
        return HealthStatus.DEGRADED

    def health_report(self) -> Health:
        return Health(
            module=self.name,
            status=self.health(),
            timestamp=datetime.now(UTC),
        )

    def __contains__(self, module_id: str) -> bool:
        return self.registry.exists(module_id)

    def __len__(self) -> int:
        return len(self.registry.list())


__all__ = [
    "Kernel",
    "KernelError",
    "DuplicateModuleError",
    "ModuleNotFoundError",
    "LifecycleState",
]
