"""Base module implementation shared by all LexMind modules."""

from dataclasses import dataclass, field

from lexmind.core.capabilities import Capability
from lexmind.core.health import Health, HealthStatus
from lexmind.core.lifecycle import LifecycleState
from lexmind.core.metadata import ModuleMetadata


@dataclass
class BaseModule:
    """Skeleton implementation of the Module contract."""

    id: str
    name: str
    version: str = "0.0.0"
    description: str = ""
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    capabilities: tuple[Capability, ...] = field(default_factory=tuple)
    metadata: ModuleMetadata = field(init=False)

    def __post_init__(self) -> None:
        self.metadata = ModuleMetadata(
            name=self.name,
            version=self.version,
            description=self.description,
            extra={"capabilities": self.capabilities},
        )
        self._state = LifecycleState.CREATED

    @property
    def state(self) -> LifecycleState:
        """Return the current lifecycle state."""
        return self._state

    def get_metadata(self) -> ModuleMetadata:
        return self.metadata

    def initialize(self) -> None:
        self._state = LifecycleState.INITIALIZED

    def start(self) -> None:
        self._state = LifecycleState.STARTED

    def stop(self) -> None:
        self._state = LifecycleState.STOPPED

    def health(self) -> Health:
        status = (
            HealthStatus.HEALTHY
            if self._state in {LifecycleState.INITIALIZED, LifecycleState.STARTED}
            else HealthStatus.UNKNOWN
        )
        return Health(module=self.id, status=status)
