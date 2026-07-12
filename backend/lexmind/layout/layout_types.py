"""Layout analysis value objects.

A document page is decomposed into typed regions (text, tables, figures,
headers, ...).  Regions use normalised bounding boxes so the coordinates are
independent of the source image resolution.  All objects are engine-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, unique


@unique
class RegionType(StrEnum):
    """Semantic type of a detected layout region."""

    TEXT = "text"
    TITLE = "title"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    FIGURE = "figure"
    IMAGE = "image"
    CAPTION = "caption"
    HEADER = "header"
    FOOTER = "footer"
    PAGE_NUMBER = "page_number"
    FORMULA = "formula"
    CODE = "code"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Normalised bounding box (all values in [0, 1])."""

    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        for value, name in (
            (self.x, "x"),
            (self.y, "y"),
            (self.width, "width"),
            (self.height, "height"),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1, got {value}")


@dataclass(frozen=True, slots=True)
class LayoutRegion:
    """A single detected region on a page."""

    region_type: RegionType
    bbox: BoundingBox
    confidence: float = 1.0
    page_number: int = 1
    order: int = 0
    text: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class LayoutResult:
    """Outcome of a layout analysis run for one page."""

    page_number: int
    regions: tuple[LayoutRegion, ...] = field(default_factory=tuple)
    analyzer: str = ""
    image_width: int = 0
    image_height: int = 0

    @property
    def region_count(self) -> int:
        """Return the number of detected regions."""
        return len(self.regions)

    @property
    def is_empty(self) -> bool:
        """Return True if no regions were detected."""
        return not self.regions


@dataclass(frozen=True, slots=True)
class LayoutAnalysisOptions:
    """Declarative request for layout analysis.

    Attributes:
        region_types: Region types to keep (empty = keep all).
        min_confidence: Drop regions below this confidence (0-1).
        merge_overlapping: Whether to drop lower-confidence regions fully
            contained in a higher-confidence one.
    """

    region_types: tuple[RegionType, ...] = field(default_factory=tuple)
    min_confidence: float = 0.0
    merge_overlapping: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")

    def keeps(self, region: LayoutRegion) -> bool:
        """Return True if *region* passes the configured filters."""
        below_confidence = region.confidence < self.min_confidence
        wrong_type = bool(self.region_types) and region.region_type not in self.region_types
        return not (below_confidence or wrong_type)
