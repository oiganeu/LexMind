"""Unit tests for the image preprocessing framework (Task 36)."""

from __future__ import annotations

import json

import pytest

from lexmind.events.event_bus import EventBus
from lexmind.ocr.preprocessing.image_operation import (
    ImageOperationError,
    ImageOperationRegistry,
    build_default_registry,
)
from lexmind.ocr.preprocessing.image_preprocessor import ImagePreprocessingPipeline
from lexmind.ocr.preprocessing.preprocessing_events import (
    ImagePreprocessingCompleted,
    ImagePreprocessingFailed,
    ImagePreprocessingStarted,
)
from lexmind.ocr.preprocessing.preprocessing_plugin import ImagePreprocessingPlugin
from lexmind.ocr.preprocessing.preprocessing_types import (
    PreprocessingOptions,
    PreprocessingResult,
)
from lexmind.plugins.plugin_capability import PluginCapability
from lexmind.plugins.plugin_state import PluginState


class RecordingEngine:
    """Stub imaging engine that carries applied transforms in the bytes."""

    def load(self, data: bytes) -> dict:
        try:
            transforms = json.loads(data.decode())
            if not isinstance(transforms, list):
                transforms = []
        except (ValueError, UnicodeDecodeError):
            transforms = []
        return {"transforms": list(transforms), "data": data}

    def save(self, image: dict) -> bytes:
        return json.dumps(image["transforms"]).encode()

    def grayscale(self, image: dict) -> dict:
        image["transforms"].append("grayscale")
        return image

    def binarize(self, image: dict, threshold: float) -> dict:
        image["transforms"].append(("binarize", threshold))
        return image

    def resize(self, image: dict, max_dim: int) -> dict:
        image["transforms"].append(("resize", max_dim))
        return image

    def deskew(self, image: dict) -> dict:
        image["transforms"].append("deskew")
        return image

    def denoise(self, image: dict) -> dict:
        image["transforms"].append("denoise")
        return image


class RecordingBus(EventBus):
    """EventBus that records published events."""

    def __init__(self) -> None:
        self.events: list = []

    def publish(self, event):  # noqa: ANN001 - test helper
        self.events.append(event)
        return []


def test_options_validation() -> None:
    with pytest.raises(ValueError):
        PreprocessingOptions(binarize_threshold=2.0)
    with pytest.raises(ValueError):
        PreprocessingOptions(resize_max_dim=-1)
    assert PreprocessingOptions().is_empty
    assert not PreprocessingOptions(grayscale=True).is_empty


def test_registry_basics() -> None:
    registry = ImageOperationRegistry()
    with pytest.raises(ValueError):
        registry.register(_BadOp())  # type: ignore[arg-type]
    engine = RecordingEngine()
    for op in build_default_registry(engine)._operations.values():
        registry.register(op)
    assert registry.has("grayscale")
    assert set(registry.registered_names()) == {
        "grayscale",
        "binarize",
        "resize",
        "deskew",
        "denoise",
    }
    with pytest.raises(ImageOperationError):
        registry.get("missing")


def test_registry_default_has_five() -> None:
    registry = build_default_registry(RecordingEngine())
    assert len(registry.registered_names()) == 5


def test_pipeline_applies_flagged_operations() -> None:
    pipeline = ImagePreprocessingPipeline(RecordingEngine())
    result = pipeline.process(
        b"img",
        PreprocessingOptions(grayscale=True, denoise=True),
    )
    assert isinstance(result, PreprocessingResult)
    assert result.applied_operations == ("grayscale", "denoise")
    assert b"grayscale" in result.image_data
    assert b"denoise" in result.image_data


def test_pipeline_explicit_order() -> None:
    pipeline = ImagePreprocessingPipeline(RecordingEngine())
    result = pipeline.process(
        b"img",
        PreprocessingOptions(enabled_operations=("binarize", "resize")),
    )
    assert result.applied_operations == ("binarize", "resize")
    assert b'["binarize", 0.5]' in result.image_data
    assert b'["resize", 0]' in result.image_data


def test_pipeline_empty_options_returns_unchanged() -> None:
    pipeline = ImagePreprocessingPipeline(RecordingEngine())
    result = pipeline.process(b"img", PreprocessingOptions())
    assert result.applied_operations == ()
    assert result.image_data == b"img"


def test_pipeline_emits_events() -> None:
    bus = RecordingBus()
    pipeline = ImagePreprocessingPipeline(RecordingEngine(), event_bus=bus)
    pipeline.process(b"img", PreprocessingOptions(grayscale=True), image_id="i1")
    started = [e for e in bus.events if isinstance(e, ImagePreprocessingStarted)]
    completed = [e for e in bus.events if isinstance(e, ImagePreprocessingCompleted)]
    assert started and completed
    assert completed[0].applied_operations == ("grayscale",)
    assert completed[0].image_id == "i1"


def test_pipeline_failure_emits_failed() -> None:
    bus = RecordingBus()

    class BrokenEngine:
        def load(self, data: bytes) -> dict:
            return {"transforms": [], "data": data}

        def save(self, image: dict) -> bytes:
            return b""

        def grayscale(self, image: dict) -> dict:
            raise RuntimeError("boom")

        def binarize(self, image: dict, threshold: float) -> dict:
            return image

        def resize(self, image: dict, max_dim: int) -> dict:
            return image

        def deskew(self, image: dict) -> dict:
            return image

        def denoise(self, image: dict) -> dict:
            return image

    pipeline = ImagePreprocessingPipeline(BrokenEngine(), event_bus=bus)
    with pytest.raises(ImageOperationError):
        pipeline.process(b"img", PreprocessingOptions(grayscale=True))
    failed = [e for e in bus.events if isinstance(e, ImagePreprocessingFailed)]
    assert failed and "boom" in failed[0].error_message


def test_plugin_wires_up() -> None:
    plugin = ImagePreprocessingPlugin(RecordingEngine())
    assert PluginCapability.IMAGE_PREPROCESSING in plugin.get_metadata().capabilities
    result = plugin.process(b"img", PreprocessingOptions(grayscale=True))
    assert result.applied_operations == ("grayscale",)
    plugin.start()
    assert plugin.state == PluginState.STARTED
    plugin.stop()
    assert plugin.state == PluginState.STOPPED


def test_plugin_rejects_none_engine() -> None:
    with pytest.raises(ValueError):
        ImagePreprocessingPlugin(None)  # type: ignore[arg-type]


class _BadOp:  # noqa: D101 - helper with empty name
    name = ""
