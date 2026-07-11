"""Configuration loader.

Loads layered YAML configuration and environment overrides, enforcing
secret exclusion from YAML sources. Application code must never read YAML
directly — it accesses configuration through the ConfigurationProvider.
"""

import os
from pathlib import Path
from typing import Any

import yaml

from lexmind.config.config_exceptions import (
    ConfigLoadError,
    SecretInConfigError,
)
from lexmind.config.config_source import ConfigSource
from lexmind.config.config_types import SourceType

_SECRET_KEY_HINTS = ("password", "secret", "api_key", "token", "private_key", "credential")


def _scan_secrets(flat: dict[str, Any], source_name: str) -> None:
    for key in flat:
        lowered = key.lower()
        if any(hint in lowered for hint in _SECRET_KEY_HINTS):
            raise SecretInConfigError(
                f"Secret-like key '{key}' found in YAML source '{source_name}'. "
                "Secrets must come from environment variables or a secret provider."
            )


def _flatten(prefix: str, data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        full = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(_flatten(full, value))
        else:
            out[full] = value
    return out


def load_yaml_source(path: Path, source_type: SourceType, name: str) -> ConfigSource:
    """Load a single YAML file into a ConfigSource, rejecting secrets."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigLoadError(f"Cannot read '{path}': {exc}") from exc
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        raise ConfigLoadError(f"Invalid YAML in '{path}': {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigLoadError(f"Configuration in '{path}' must be a mapping.")
    _scan_secrets(_flatten("", data), name)
    return ConfigSource(name=name, source_type=source_type, data=data, path=str(path))


def load_env_overrides(prefix: str = "LEXMIND_") -> ConfigSource:
    """Collect environment variables with the given prefix as overrides.

    Variables such as ``LEXMIND_OCR__LANGUAGES`` map to nested keys using
    a double underscore separator. Secrets via env are allowed.
    """
    overrides: dict[str, Any] = {}
    for raw_key, value in os.environ.items():
        if not raw_key.startswith(prefix):
            continue
        relative = raw_key[len(prefix) :].lower()
        if not relative:
            continue
        parts = relative.split("__")
        target: dict[str, Any] = overrides
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = _coerce(value)
    return ConfigSource(name="env_vars", source_type=SourceType.RUNTIME, data=overrides)


def _coerce(value: str) -> object:
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    if value.isdigit():
        return int(value)
    return value


def merge_sources(sources: list[ConfigSource]) -> dict[str, Any]:
    """Merge sources by ascending precedence priority."""
    ordered = sorted(sources, key=lambda s: s.priority)
    merged: dict[str, Any] = {}
    for source in ordered:
        from lexmind.config.config_validator import deep_merge

        merged = deep_merge(merged, source.data)
    return merged
