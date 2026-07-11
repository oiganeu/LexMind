"""Plugin registry."""

from typing import Any

from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_exceptions import DuplicatePluginError


class PluginRegistry:
    """Stores plugins by id and supports capability lookup."""

    def __init__(self) -> None:
        self._plugins: dict[str, Any] = {}

    def register(self, plugin: Any) -> None:
        plugin_id = getattr(plugin, "id", None)
        if plugin_id is None:
            raise DuplicatePluginError("Plugin has no id attribute.")
        if plugin_id in self._plugins:
            raise DuplicatePluginError(f"Plugin '{plugin_id}' is already registered.")
        self._plugins[plugin_id] = plugin

    def unregister(self, plugin_id: str) -> None:
        self._plugins.pop(plugin_id, None)

    def find(self, plugin_id: str) -> object | None:
        return self._plugins.get(plugin_id)

    def find_by_capability(self, capability: PluginCapability) -> list[object]:
        return [p for p in self._plugins.values() if capability in getattr(p, "capabilities", ())]

    def list(self) -> list[Any]:
        return list(self._plugins.values())

    def exists(self, plugin_id: str) -> bool:
        return plugin_id in self._plugins

    def clear(self) -> None:
        self._plugins.clear()
