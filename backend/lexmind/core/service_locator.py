"""Service locator for shared kernel services."""

from typing import Any


class ServiceLocator:
    """Lightweight registry of shared services by name.

    Used to expose shared interfaces used by every component without
    introducing hard dependencies between modules.
    """

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service

    def get(self, name: str) -> Any:
        if name not in self._services:
            raise KeyError(f"Service '{name}' is not registered.")
        return self._services[name]

    def has(self, name: str) -> bool:
        return name in self._services

    def clear(self) -> None:
        self._services.clear()
