"""Unit tests for the LexMind Plugin Framework."""

from lexmind.plugins import (
    BasePlugin,
    CircularDependencyError,
    IncompatibleKernelError,
    MissingDependencyError,
    PluginCapability,
    PluginManager,
    PluginManifest,
    PluginRegistry,
    PluginState,
)
from lexmind.plugins.plugin_exceptions import DuplicatePluginError


class SamplePlugin(BasePlugin):
    def __init__(self, pid: str, caps=(), deps=(), enabled=True) -> None:
        super().__init__(
            id=pid,
            name=pid,
            version="1.0.0",
            capabilities=caps,
            dependencies=deps,
            enabled=enabled,
        )


def test_plugin_registration() -> None:
    reg = PluginRegistry()
    reg.register(SamplePlugin("p1"))
    assert reg.exists("p1")
    assert reg.find("p1") is not None
    assert len(reg.list()) == 1


def test_duplicate_plugin_rejection() -> None:
    reg = PluginRegistry()
    reg.register(SamplePlugin("p1"))
    try:
        reg.register(SamplePlugin("p1"))
    except DuplicatePluginError:
        pass
    else:
        raise AssertionError("expected DuplicatePluginError")


def test_capability_lookup() -> None:
    reg = PluginRegistry()
    reg.register(SamplePlugin("ocr1", caps=(PluginCapability.OCR,)))
    reg.register(SamplePlugin("llm1", caps=(PluginCapability.LLM,)))
    found = reg.find_by_capability(PluginCapability.OCR)
    assert [p.id for p in found] == ["ocr1"]


def test_manifest_parsing() -> None:
    yaml_text = """
id: my-plugin
version: 2.3.1
author: Jane
description: Example
license: MIT
capabilities:
  - ocr
  - parser
dependencies:
  - core
entrypoint: my_plugin:Plugin
minimum_kernel_version: 0.1.0
"""
    manifest = PluginManifest.from_yaml(yaml_text)
    assert manifest.id == "my-plugin"
    assert manifest.version == "2.3.1"
    assert PluginCapability.OCR in manifest.capabilities
    assert PluginCapability.PARSER in manifest.capabilities
    assert "core" in manifest.dependencies
    assert manifest.entrypoint == "my_plugin:Plugin"
    assert manifest.minimum_kernel_version == "0.1.0"


def test_dependency_validation_missing() -> None:
    manager = PluginManager(kernel_version="0.1.0")
    manager.register(SamplePlugin("needs-dep", deps=("missing",)))
    try:
        manager.validate()
    except MissingDependencyError:
        pass
    else:
        raise AssertionError("expected MissingDependencyError")


def test_circular_dependency_detection() -> None:
    reg = PluginRegistry()
    reg.register(SamplePlugin("a", deps=("b",)))
    reg.register(SamplePlugin("b", deps=("a",)))
    try:
        from lexmind.plugins import validate_dependencies

        validate_dependencies(reg)
    except CircularDependencyError:
        pass
    else:
        raise AssertionError("expected CircularDependencyError")


def test_lifecycle_transitions() -> None:
    plugin = SamplePlugin("life")
    assert plugin.state == PluginState.DISCOVERED
    plugin.initialize(None)
    assert plugin.state == PluginState.INITIALIZED
    plugin.start()
    assert plugin.state == PluginState.STARTED
    plugin.stop()
    assert plugin.state == PluginState.STOPPED
    plugin.dispose()
    assert plugin.state == PluginState.UNINSTALLED


def test_disabled_plugin_not_loaded() -> None:
    manager = PluginManager(kernel_version="0.1.0")
    plugin = SamplePlugin("disabled", enabled=False)
    manager.register(plugin)
    try:
        manager.load(plugin)
    except Exception as exc:
        assert "disabled" in str(exc).lower()
    else:
        raise AssertionError("expected disabled plugin error")


def test_version_compatibility() -> None:
    from lexmind.plugins import PluginMetadata

    manager = PluginManager(kernel_version="0.2.0")
    compatible = SamplePlugin("ok", deps=())
    compatible.metadata = PluginMetadata(
        id="ok",
        name="ok",
        version="1.0.0",
        minimum_kernel_version="0.1.0",
        maximum_kernel_version="0.3.0",
    )
    manager.register(compatible)

    incompatible = SamplePlugin("bad", deps=())
    incompatible.metadata = PluginMetadata(
        id="bad",
        name="bad",
        version="1.0.0",
        minimum_kernel_version="1.0.0",
    )
    try:
        manager.register(incompatible)
    except IncompatibleKernelError:
        pass
    else:
        raise AssertionError("expected IncompatibleKernelError")
