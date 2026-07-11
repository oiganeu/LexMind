"""Configuration manager.

Orchestrates loading, validation, typed access, runtime overrides, reload,
and event publishing. This is the single entry point application code uses.
"""

from pathlib import Path
from typing import Any

from lexmind.config.config_events import (
    CONFIGURATION_CHANGED,
    CONFIGURATION_LOADED,
    CONFIGURATION_VALIDATION_FAILED,
)
from lexmind.config.config_exceptions import ConfigValidationError
from lexmind.config.config_loader import (
    load_env_overrides,
    load_yaml_source,
    merge_sources,
)
from lexmind.config.config_provider import ConfigurationProvider
from lexmind.config.config_registry import ROOT_MODEL
from lexmind.config.config_source import ConfigSource
from lexmind.config.config_types import Environment, SourceType
from lexmind.config.config_validator import (
    check_deprecated,
    check_unknown_sections,
    deep_merge,
)
from lexmind.config.environment import detect_environment
from lexmind.events.event import Event
from lexmind.events.event_bus import EventBus


class ConfigManager:
    """Loads, validates, and serves configuration."""

    def __init__(
        self,
        config_dir: str | Path,
        environment: Environment | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._config_dir = Path(config_dir)
        self._environment = environment or detect_environment()
        self._event_bus = event_bus
        self._provider: ConfigurationProvider | None = None
        self._runtime_overrides: dict[str, Any] = {}

    @property
    def provider(self) -> ConfigurationProvider:
        if self._provider is None:
            raise ConfigValidationError("Configuration has not been loaded.")
        return self._provider

    def load(self) -> ConfigurationProvider:
        sources = self._collect_sources()
        merged = merge_sources(sources)
        check_unknown_sections(merged)
        check_deprecated(merged)
        if self._runtime_overrides:
            merged = deep_merge(merged, self._runtime_overrides)
        try:
            config = ROOT_MODEL.model_validate(merged)
        except Exception as exc:  # noqa: BLE001 - surface as config error
            self._publish(CONFIGURATION_VALIDATION_FAILED, {"error": str(exc)})
            raise ConfigValidationError(str(exc)) from exc
        self._provider = ConfigurationProvider(config)
        self._publish(CONFIGURATION_LOADED, {"environment": self._environment.value})
        return self._provider

    def reload(self) -> ConfigurationProvider:
        return self.load()

    def set_override(self, dotted_key: str, value: Any) -> None:
        """Apply a runtime override without modifying YAML files."""
        target = self._runtime_overrides
        parts = dotted_key.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
        if self._provider is not None:
            self.load()
            self._publish(CONFIGURATION_CHANGED, {"key": dotted_key})

    def _collect_sources(self) -> list[ConfigSource]:
        sources: list[ConfigSource] = []
        defaults = self._config_dir / "default.yaml"
        if defaults.exists():
            sources.append(load_yaml_source(defaults, SourceType.DEFAULT, "default"))
        env_file = self._config_dir / f"{self._environment.value}.yaml"
        if env_file.exists():
            sources.append(
                load_yaml_source(env_file, SourceType.ENVIRONMENT, self._environment.value)
            )
        workspace = self._config_dir / "workspace.yaml"
        if workspace.exists():
            sources.append(load_yaml_source(workspace, SourceType.WORKSPACE, "workspace"))
        sources.append(load_env_overrides())
        return sources

    def _publish(self, name: str, payload: dict[str, Any]) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(Event(name=name, source_module="config", payload=payload))
