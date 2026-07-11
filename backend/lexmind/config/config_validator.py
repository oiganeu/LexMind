"""Configuration validation and merge utilities."""

from typing import Any

from lexmind.config.config_exceptions import (
    DeprecatedConfigKeyError,
    UnknownConfigKeyError,
)
from lexmind.config.config_registry import SECTION_MODELS
from lexmind.config.config_schema import DEPRECATED_KEYS


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` into ``base`` (returns a new dict)."""
    result: dict[str, Any] = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _flatten(prefix: str, data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        full = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(_flatten(full, value))
        else:
            out[full] = value
    return out


def check_deprecated(data: dict[str, Any]) -> None:
    """Raise DeprecatedConfigKeyError for any deprecated flattened key."""
    flat = _flatten("", data)
    for key in DEPRECATED_KEYS:
        if key in flat:
            raise DeprecatedConfigKeyError(f"Deprecated configuration key: '{key}'.")


def check_unknown_sections(data: dict[str, Any]) -> None:
    """Raise UnknownConfigKeyError for top-level sections not in the schema."""
    known = set(SECTION_MODELS) | {"version"}
    for key in data:
        if key not in known:
            raise UnknownConfigKeyError(f"Unknown configuration section: '{key}'.")
