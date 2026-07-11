"""Module registry.

Stores and resolves modules by id. No concrete module implementations
are referenced here.
"""

from dataclasses import dataclass, field

from lexmind.core.interfaces import Module
from lexmind.exceptions import LexMindError


class DuplicateModuleError(LexMindError):
    """Raised when registering a module id that already exists."""


class ModuleNotFoundError(LexMindError):
    """Raised when a module id is not registered."""


@dataclass
class ModuleRegistry:
    """In-memory registry of modules."""

    _modules: dict[str, Module] = field(default_factory=dict)

    def register(self, module: Module) -> None:
        if module.id in self._modules:
            raise DuplicateModuleError(f"Module '{module.id}' is already registered.")
        self._modules[module.id] = module

    def unregister(self, module_id: str) -> None:
        if module_id not in self._modules:
            raise ModuleNotFoundError(f"Module '{module_id}' is not registered.")
        del self._modules[module_id]

    def get(self, module_id: str) -> Module:
        if module_id not in self._modules:
            raise ModuleNotFoundError(f"Module '{module_id}' is not registered.")
        return self._modules[module_id]

    def list(self) -> list[Module]:
        return list(self._modules.values())

    def exists(self, module_id: str) -> bool:
        return module_id in self._modules
