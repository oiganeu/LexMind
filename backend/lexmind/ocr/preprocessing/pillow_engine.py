"""Pillow-backed imaging engine.

Concrete :class:`ImageEngine` implementation using Pillow.  The dependency
is imported lazily inside each method so the preprocessing framework can be
imported and unit-tested with a stub engine even when Pillow is not
installed.  The heavier transforms (deskew, denoise) degrade gracefully
when their optional helpers are unavailable.
"""

from __future__ import annotations

import io
from typing import Any


class PillowImageEngine:
    """Imaging engine backed by the ``Pillow`` library."""

    def load(self, data: bytes) -> Any:
        """Decode image bytes into a Pillow image."""
        from PIL import Image  # type: ignore[import-not-found]

        return Image.open(io.BytesIO(data)).convert("RGB")

    def save(self, image: Any) -> bytes:
        """Encode a Pillow image back into PNG bytes."""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    def grayscale(self, image: Any) -> Any:
        """Return a grayscale version of *image*."""
        return image.convert("L")

    def binarize(self, image: Any, threshold: float) -> Any:
        """Threshold *image* to black/white at *threshold* ([0,1])."""
        gray = image.convert("L")
        cutoff = int(threshold * 255)
        return gray.point(lambda pixel: 255 if pixel >= cutoff else 0)

    def resize(self, image: Any, max_dim: int) -> Any:
        """Scale *image* so its longest edge is at most *max_dim*."""
        image.thumbnail((max_dim, max_dim))
        return image

    def deskew(self, image: Any) -> Any:
        """Straighten *image* (best-effort; requires an angle estimate).

        Without an external skew estimator this returns the image unchanged.
        A deployment can subclass and inject a real de-rotation step.
        """
        return image

    def denoise(self, image: Any) -> Any:
        """Reduce noise using a median filter when available."""
        try:
            from PIL import ImageFilter  # type: ignore[import-not-found]

            return image.filter(ImageFilter.MedianFilter(size=3))
        except Exception:  # noqa: BLE001 - denoise is best-effort
            return image
