"""Configuration source abstraction."""

from dataclasses import dataclass, field
from typing import Any

from lexmind.config.config_types import SourceType


@dataclass
class ConfigSource:
    """A single layered configuration source."""

    name: str
    source_type: SourceType
    data: dict[str, Any] = field(default_factory=dict)
    path: str | None = None

    @property
    def priority(self) -> int:
        from lexmind.config.config_types import SOURCE_PRIORITY

        return SOURCE_PRIORITY[self.source_type]
