"""Unit tests for the LexMind Core Kernel using mock modules."""

from lexmind.core.bootstrap import bootstrap, shutdown
from lexmind.core.capabilities import Capability
from lexmind.core.health import HealthStatus
from lexmind.core.kernel import Kernel
from lexmind.core.lifecycle import LifecycleState
from lexmind.core.module import BaseModule
from lexmind.core.registry import (
    DuplicateModuleError,
    ModuleNotFoundError,
    ModuleRegistry,
)
from lexmind.exceptions import LexMindError


class MockModule(BaseModule):
    def __init__(self, mid: str, caps: tuple[Capability, ...] = ()) -> None:
        super().__init__(
            id=mid,
            name=f"Mock {mid}",
            version="1.0.0",
            capabilities=caps,
        )


def test_kernel_creation() -> None:
    kernel = Kernel()
    assert kernel.name == "LexMind Kernel"
    assert len(kernel) == 0


def test_module_registration() -> None:
    registry = ModuleRegistry()
    registry.register(MockModule("a"))
    assert registry.exists("a")
    assert len(registry.list()) == 1
    assert registry.get("a").id == "a"


def test_duplicate_registration_detection() -> None:
    registry = ModuleRegistry()
    registry.register(MockModule("a"))
    try:
        registry.register(MockModule("a"))
    except DuplicateModuleError as exc:
        assert isinstance(exc, LexMindError)
    else:
        raise AssertionError("expected DuplicateModuleError")


def test_unregister_missing_raises() -> None:
    registry = ModuleRegistry()
    try:
        registry.unregister("missing")
    except ModuleNotFoundError:
        pass
    else:
        raise AssertionError("expected ModuleNotFoundError")


def test_lifecycle_transitions() -> None:
    module = MockModule("x")
    assert module.state == LifecycleState.CREATED
    module.initialize()
    assert module.state == LifecycleState.INITIALIZED
    module.start()
    assert module.state == LifecycleState.STARTED
    module.stop()
    assert module.state == LifecycleState.STOPPED


def test_capability_registration() -> None:
    kernel = Kernel()
    kernel.register_module(MockModule("ocr1", (Capability.OCR,)))
    assert kernel.capabilities[Capability.OCR.value].id == "ocr1"


def test_health_object_creation() -> None:
    module = MockModule("h")
    module.start()
    health = module.health()
    assert health.module == "h"
    assert health.status == HealthStatus.HEALTHY
    assert health.is_healthy()


def test_bootstrap_runs_modules() -> None:
    kernel = bootstrap([MockModule("m1"), MockModule("m2", (Capability.PARSER,))])
    assert len(kernel) == 2
    assert kernel.health() == HealthStatus.HEALTHY
    assert kernel.health_report().status == HealthStatus.HEALTHY
    shutdown(kernel)
    assert kernel.registry.get("m1").state == LifecycleState.STOPPED
