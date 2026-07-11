"""Core interfaces (ports) for the LexMind kernel.

These protocols define the contracts every module, the kernel, the registry,
and capability/health/configuration providers must satisfy. No concrete
implementations live here.
"""

from typing import Any, Protocol, runtime_checkable

from lexmind.core.capabilities import Capability
from lexmind.core.health import Health, HealthStatus
from lexmind.core.metadata import ModuleMetadata


@runtime_checkable
class Module(Protocol):
    """Contract every LexMind module must satisfy."""

    id: str
    name: str
    version: str
    description: str
    dependencies: tuple[str, ...]
    capabilities: tuple[Capability, ...]

    def get_metadata(self) -> ModuleMetadata: ...

    def initialize(self) -> None: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def health(self) -> Health: ...


@runtime_checkable
class HealthProvider(Protocol):
    """Provides health reporting."""

    def health(self) -> Health: ...


@runtime_checkable
class CapabilityProvider(Protocol):
    """Exposes capabilities."""

    def get_capabilities(self) -> tuple[Capability, ...]: ...


@runtime_checkable
class ConfigurationProvider(Protocol):
    """Exposes configuration values."""

    def get(self, key: str, default: Any = None) -> Any: ...


@runtime_checkable
class Registry(Protocol):
    """Stores and resolves modules."""

    def register(self, module: Module) -> None: ...

    def unregister(self, module_id: str) -> None: ...

    def get(self, module_id: str) -> Module: ...

    def list(self) -> list[Module]: ...

    def exists(self, module_id: str) -> bool: ...


@runtime_checkable
class Kernel(Protocol):
    """Top-level coordinator."""

    def register_module(self, module: Module) -> None: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def health(self) -> HealthStatus: ...
