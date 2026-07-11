"""Plugin interface and base implementation."""

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from lexmind.core.health import Health, HealthStatus
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_metadata import PluginMetadata
from lexmind.plugins.plugin_state import PluginState


@runtime_checkable
class Plugin(Protocol):
    """Contract every LexMind plugin satisfies."""

    id: str
    name: str
    version: str

    def get_metadata(self) -> PluginMetadata: ...

    def initialize(self, context: Any) -> None: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def dispose(self) -> None: ...

    def health(self) -> Health: ...


@dataclass
class BasePlugin:
    """Skeleton implementation of the Plugin contract."""

    id: str
    name: str
    version: str
    display_name: str = ""
    author: str = "Unknown"
    license: str = "Apache-2.0"
    homepage: str = ""
    repository: str = ""
    description: str = ""
    capabilities: tuple[PluginCapability, ...] = field(default_factory=tuple)
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    supported_platforms: tuple[str, ...] = field(default_factory=tuple)
    minimum_kernel_version: str | None = None
    maximum_kernel_version: str | None = None
    experimental: bool = False
    enabled: bool = True
    metadata: PluginMetadata = field(init=False)

    def __post_init__(self) -> None:
        self.metadata = PluginMetadata(
            id=self.id,
            name=self.name,
            display_name=self.display_name or self.name,
            version=self.version,
            author=self.author,
            license=self.license,
            homepage=self.homepage,
            repository=self.repository,
            description=self.description,
            capabilities=self.capabilities,
            dependencies=self.dependencies,
            supported_platforms=self.supported_platforms,
            minimum_kernel_version=self.minimum_kernel_version,
            maximum_kernel_version=self.maximum_kernel_version,
            experimental=self.experimental,
            enabled=self.enabled,
        )
        self._state = PluginState.DISCOVERED
        self._context: Any = None

    @property
    def state(self) -> PluginState:
        """Return the current plugin state."""
        return self._state

    def get_metadata(self) -> PluginMetadata:
        return self.metadata

    def initialize(self, context: Any) -> None:
        self._context = context
        self._state = PluginState.INITIALIZED

    def start(self) -> None:
        self._state = PluginState.STARTED

    def stop(self) -> None:
        self._state = PluginState.STOPPED

    def dispose(self) -> None:
        self._state = PluginState.UNINSTALLED

    def health(self) -> Health:
        healthy = self._state in {PluginState.INITIALIZED, PluginState.STARTED}
        return Health(
            module=self.id,
            status=HealthStatus.HEALTHY if healthy else HealthStatus.UNKNOWN,
        )
