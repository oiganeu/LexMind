"""Image preprocessing value objects.

Options describe *what* preprocessing to apply; the result describes *what*
was applied and the resulting image bytes.  Both are engine-agnostic so the
preprocessing framework can be tested without any imaging library installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PreprocessingOptions:
    """Declarative description of the preprocessing to apply.

    Attributes:
        grayscale: Convert the image to grayscale.
        binarize: Threshold the image to black/white.
        binarize_threshold: Threshold in [0, 1] used when binarizing.
        resize_max_dim: Longest edge in pixels (0 = no resize).
        deskew: Straighten a rotated/curved page.
        denoise: Reduce noise / speckles.
        enabled_operations: Explicit ordered operation names.  When set, the
            options flags above are ignored and this order is used.
    """

    grayscale: bool = False
    binarize: bool = False
    binarize_threshold: float = 0.5
    resize_max_dim: int = 0
    deskew: bool = False
    denoise: bool = False
    enabled_operations: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0.0 <= self.binarize_threshold <= 1.0:
            raise ValueError("binarize_threshold must be between 0 and 1")
        if self.resize_max_dim < 0:
            raise ValueError("resize_max_dim must be non-negative")

    @property
    def is_empty(self) -> bool:
        """Return True if no preprocessing is requested."""
        return not (
            self.grayscale
            or self.binarize
            or self.deskew
            or self.denoise
            or self.resize_max_dim > 0
            or self.enabled_operations
        )


@dataclass(frozen=True, slots=True)
class PreprocessingResult:
    """Outcome of a preprocessing run."""

    image_data: bytes
    applied_operations: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def was_modified(self) -> bool:
        """Return True if at least one operation was applied."""
        return bool(self.applied_operations)
