"""Imaging engine contract for preprocessing.

All pixel-level work is delegated to an :class:`ImageEngine`.  The default
implementation binds to Pillow but imports it lazily, so the preprocessing
framework (and its tests) work without the native dependency.  Operations
and the pipeline depend only on this Protocol.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ImageEngine(Protocol):
    """Abstraction over a concrete imaging library."""

    def load(self, data: bytes) -> Any:
        """Decode image bytes into an engine-specific handle."""
        ...

    def save(self, image: Any) -> bytes:
        """Encode an engine-specific handle back into image bytes."""
        ...

    def grayscale(self, image: Any) -> Any:
        """Return a grayscale version of *image*."""
        ...

    def binarize(self, image: Any, threshold: float) -> Any:
        """Return a black/white version of *image* at *threshold* ([0,1])."""
        ...

    def resize(self, image: Any, max_dim: int) -> Any:
        """Return *image* scaled so its longest edge is *max_dim* pixels."""
        ...

    def deskew(self, image: Any) -> Any:
        """Return a de-rotated / straightened version of *image*."""
        ...

    def denoise(self, image: Any) -> Any:
        """Return a noise-reduced version of *image*."""
        ...
