"""Preprocessing operations and their registry.

An :class:`ImageOperation` is a single, named, reversible-in-principle
transform applied to image bytes.  Concrete operations delegate the actual
pixel work to an injected :class:`ImageEngine`.  The
:class:`ImageOperationRegistry` maps operation names to implementations so
the pipeline can be configured declaratively.
"""

from __future__ import annotations

import structlog

from lexmind.ocr.preprocessing.image_engine import ImageEngine
from lexmind.ocr.preprocessing.preprocessing_types import PreprocessingOptions

logger = structlog.get_logger(__name__)


class ImageOperationError(Exception):
    """Raised when a preprocessing operation fails."""


class ImageOperation:
    """Base class for named preprocessing operations."""

    name: str = "operation"

    def __init__(self, engine: ImageEngine) -> None:
        self._engine = engine

    def apply(self, image_data: bytes, options: PreprocessingOptions) -> bytes:
        """Apply the operation to *image_data* and return new bytes."""
        image = self._engine.load(image_data)
        image = self._transform(image, options)
        return self._engine.save(image)

    def _transform(self, image: object, options: PreprocessingOptions) -> object:
        """Perform the engine-specific transform.  Override in subclasses."""
        raise NotImplementedError


class GrayscaleOperation(ImageOperation):
    """Converts the image to grayscale."""

    name = "grayscale"

    def _transform(self, image: object, options: PreprocessingOptions) -> object:
        return self._engine.grayscale(image)


class BinarizeOperation(ImageOperation):
    """Threshold the image to black and white."""

    name = "binarize"

    def _transform(self, image: object, options: PreprocessingOptions) -> object:
        return self._engine.binarize(image, options.binarize_threshold)


class ResizeOperation(ImageOperation):
    """Scale the image so its longest edge fits ``resize_max_dim``."""

    name = "resize"

    def _transform(self, image: object, options: PreprocessingOptions) -> object:
        return self._engine.resize(image, options.resize_max_dim)


class DeskewOperation(ImageOperation):
    """Straighten a rotated or curved page."""

    name = "deskew"

    def _transform(self, image: object, options: PreprocessingOptions) -> object:
        return self._engine.deskew(image)


class DenoiseOperation(ImageOperation):
    """Reduce noise and speckles."""

    name = "denoise"

    def _transform(self, image: object, options: PreprocessingOptions) -> object:
        return self._engine.denoise(image)


class ImageOperationRegistry:
    """Registry mapping operation names to :class:`ImageOperation` instances."""

    def __init__(self) -> None:
        self._operations: dict[str, ImageOperation] = {}

    def register(self, operation: ImageOperation) -> None:
        """Register an operation instance under its ``name``."""
        if not operation.name:
            raise ValueError("operation name must not be empty")
        self._operations[operation.name] = operation

    def get(self, name: str) -> ImageOperation:
        """Return the operation registered under *name*."""
        operation = self._operations.get(name)
        if operation is None:
            raise ImageOperationError(f"No operation registered for '{name}'")
        return operation

    def has(self, name: str) -> bool:
        """Return True if an operation is registered under *name*."""
        return name in self._operations

    def registered_names(self) -> list[str]:
        """Return the registered operation names."""
        return sorted(self._operations)


def build_default_registry(engine: ImageEngine) -> ImageOperationRegistry:
    """Create a registry populated with the standard operations."""
    registry = ImageOperationRegistry()
    for operation in (
        GrayscaleOperation(engine),
        BinarizeOperation(engine),
        ResizeOperation(engine),
        DeskewOperation(engine),
        DenoiseOperation(engine),
    ):
        registry.register(operation)
    return registry
