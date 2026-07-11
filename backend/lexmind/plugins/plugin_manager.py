"""Plugin manager.

Orchestrates plugin discovery, registration, dependency validation,
version compatibility, and lifecycle. No concrete plugins are implemented
here — only the framework.
"""

from typing import Any

from lexmind.plugins.plugin_exceptions import (
    CircularDependencyError,
    DuplicatePluginError,
    IncompatibleKernelError,
    MissingDependencyError,
)
from lexmind.plugins.plugin_registry import PluginRegistry


def parse_version(version: str) -> tuple[int, ...]:
    """Parse a dotted version string into a comparable tuple."""
    parts: list[int] = []
    for token in version.split("."):
        num = ""
        for ch in token:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    return tuple(parts)


def version_in_range(
    version: str,
    minimum: str | None,
    maximum: str | None,
) -> bool:
    """Return True if version satisfies optional inclusive bounds."""
    current = parse_version(version)
    too_low = minimum is not None and current < parse_version(minimum)
    too_high = maximum is not None and current > parse_version(maximum)
    return not (too_low or too_high)


def validate_dependencies(registry: PluginRegistry) -> None:
    """Validate the plugin dependency graph.

    Raises MissingDependencyError for unmet dependencies and
    CircularDependencyError for cycles.
    """
    plugins = {p.id: p for p in registry.list()}

    for plugin_id, plugin in plugins.items():
        for dep in getattr(plugin, "dependencies", ()):
            if dep not in plugins:
                raise MissingDependencyError(
                    f"Plugin '{plugin_id}' requires missing dependency '{dep}'."
                )

    _detect_cycle(plugins)


def _detect_cycle(
    plugins: dict[str, object],
    start: str | None = None,
) -> None:
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = dict.fromkeys(plugins, WHITE)

    def visit(node: str, stack: list[str]) -> None:
        color[node] = GRAY
        for dep in getattr(plugins[node], "dependencies", ()):
            if dep not in color:
                continue
            if color[dep] == GRAY:
                cycle = " -> ".join(stack + [dep])
                raise CircularDependencyError(f"Circular plugin dependency: {cycle}")
            if color[dep] == WHITE:
                visit(dep, stack + [dep])
        color[node] = BLACK

    roots = [start] if start else list(plugins)
    for node in roots:
        if color.get(node, WHITE) == WHITE:
            visit(node, [node])


class PluginManager:
    """Coordinates the plugin lifecycle and dependency graph."""

    def __init__(self, kernel_version: str) -> None:
        self.kernel_version = kernel_version
        self.registry = PluginRegistry()

    def register(self, plugin: Any) -> None:
        plugin_id = getattr(plugin, "id", None)
        if plugin_id is None:
            raise DuplicatePluginError("Plugin has no id attribute.")
        metadata = getattr(plugin, "metadata", None)
        if metadata is not None and not metadata.is_compatible_kernel(self.kernel_version):
            raise IncompatibleKernelError(
                f"Plugin '{plugin_id}' is incompatible with kernel " f"{self.kernel_version}."
            )
        self.registry.register(plugin)

    def load(self, plugin: Any, context: Any | None = None) -> None:
        """Initialize and start a plugin if enabled."""
        metadata = getattr(plugin, "metadata", None)
        if metadata is not None and not metadata.enabled:
            from lexmind.plugins.plugin_exceptions import PluginDisabledError

            raise PluginDisabledError(f"Plugin '{plugin.id}' is disabled.")
        if hasattr(plugin, "initialize"):
            plugin.initialize(context)
        if hasattr(plugin, "start"):
            plugin.start()

    def unload(self, plugin_id: str) -> None:
        plugin: Any = self.registry.find(plugin_id)
        if plugin is not None and hasattr(plugin, "stop"):
            plugin.stop()
            self.registry.unregister(plugin_id)

    def validate(self) -> None:
        validate_dependencies(self.registry)
