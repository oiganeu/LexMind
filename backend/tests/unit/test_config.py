"""Tests for the configuration management system."""

from pathlib import Path

import pytest

from lexmind.config.config_exceptions import (
    ConfigValidationError,
    DeprecatedConfigKeyError,
    SecretInConfigError,
    UnknownConfigKeyError,
)
from lexmind.config.config_loader import load_env_overrides, load_yaml_source
from lexmind.config.config_manager import ConfigManager
from lexmind.config.config_source import SourceType
from lexmind.config.config_types import Environment
from lexmind.config.config_validator import (
    check_deprecated,
    check_unknown_sections,
    deep_merge,
)
from lexmind.events.event_bus import EventBus


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_deep_merge_nested() -> None:
    base = {"a": {"x": 1, "y": 2}, "b": 3}
    override = {"a": {"y": 20, "z": 30}, "c": 4}
    result = deep_merge(base, override)
    assert result == {"a": {"x": 1, "y": 20, "z": 30}, "b": 3, "c": 4}


def test_precedence_env_over_default(tmp_path: Path) -> None:
    _write(tmp_path / "default.yaml", "version: 1\nsystem:\n  debug: false\n")
    _write(tmp_path / "development.yaml", "version: 1\nsystem:\n  debug: true\n")
    manager = ConfigManager(tmp_path, environment=Environment.DEVELOPMENT)
    provider = manager.load()
    assert provider.system.debug is True


def test_validation_error_on_bad_type(tmp_path: Path) -> None:
    _write(tmp_path / "default.yaml", "version: 1\napi:\n  port: 70000\n")
    manager = ConfigManager(tmp_path, environment=Environment.DEVELOPMENT)
    with pytest.raises(ConfigValidationError):
        manager.load()


def test_unknown_section_rejected() -> None:
    with pytest.raises(UnknownConfigKeyError):
        check_unknown_sections({"bogus": {"x": 1}})


def test_deprecated_key_rejected() -> None:
    with pytest.raises(DeprecatedConfigKeyError):
        check_deprecated({"logging": {"colors": True}})


def test_secret_in_yaml_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path / "default.yaml", "version: 1\napi:\n  api_key: leaked\n")
    with pytest.raises(SecretInConfigError):
        load_yaml_source(path, SourceType.DEFAULT, "default")


def test_env_var_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path / "default.yaml", "version: 1\nsystem:\n  debug: false\n")
    monkeypatch.setenv("LEXMIND_SYSTEM__DEBUG", "true")
    manager = ConfigManager(tmp_path, environment=Environment.DEVELOPMENT)
    provider = manager.load()
    assert provider.system.debug is True


def test_env_var_coercion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LEXMIND_API__PORT", "9001")
    source = load_env_overrides()
    assert source.data["api"]["port"] == 9001


def test_runtime_override(tmp_path: Path) -> None:
    _write(tmp_path / "default.yaml", "version: 1\napi:\n  port: 8000\n")
    manager = ConfigManager(tmp_path, environment=Environment.DEVELOPMENT)
    manager.load()
    manager.set_override("api.port", 8123)
    assert manager.provider.api.port == 8123


def test_events_published_on_load(tmp_path: Path) -> None:
    _write(tmp_path / "default.yaml", "version: 1\n")
    bus = EventBus()
    received: list[str] = []
    bus.subscribe_fn("configuration.loaded", lambda e: received.append(e.name))
    manager = ConfigManager(tmp_path, environment=Environment.DEVELOPMENT, event_bus=bus)
    manager.load()
    assert "configuration.loaded" in received


def test_defaults_applied_without_files(tmp_path: Path) -> None:
    manager = ConfigManager(tmp_path, environment=Environment.TESTING)
    provider = manager.load()
    assert provider.api.port == 8000
    assert provider.system.app_name == "LexMind"
