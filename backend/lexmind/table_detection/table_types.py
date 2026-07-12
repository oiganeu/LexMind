"""Table detection value objects.

Table detection refines the document layout: it locates table regions and,
for each, the grid of cells.  A :class:`TableRegion` carries a
:class:`TableGrid` of :class:`TableCell` objects positioned by row/column.
All objects are engine-agnostic and reuse the normalised
:class:`~lexmind.layout.layout_types.BoundingBox`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lexmind.layout.layout_types import BoundingBox


@dataclass(frozen=True, slots=True)
class TableCell:
    """A single cell within a table grid."""

    row: int
    column: int
    bbox: BoundingBox
    text: str = ""
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if self.row < 0 or self.column < 0:
            raise ValueError("row and column must be non-negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class TableGrid:
    """The rows/columns structure of a detected table."""

    rows: int
    columns: int
    cells: tuple[TableCell, ...] = field(default_factory=tuple)

    @property
    def cell_count(self) -> int:
        """Return the number of cells in the grid."""
        return len(self.cells)

    def cell_at(self, row: int, column: int) -> TableCell | None:
        """Return the cell at *(row, column)* or ``None``."""
        for cell in self.cells:
            if cell.row == row and cell.column == column:
                return cell
        return None


@dataclass(frozen=True, slots=True)
class TableRegion:
    """A detected table on a page, with its grid."""

    bbox: BoundingBox
    grid: TableGrid
    confidence: float = 1.0
    page_number: int = 1

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class TableDetectionResult:
    """Outcome of a table detection run for one page."""

    page_number: int
    tables: tuple[TableRegion, ...] = field(default_factory=tuple)
    detector: str = ""

    @property
    def table_count(self) -> int:
        """Return the number of detected tables."""
        return len(self.tables)

    @property
    def is_empty(self) -> bool:
        """Return True if no tables were detected."""
        return not self.tables


@dataclass(frozen=True, slots=True)
class TableDetectionOptions:
    """Declarative request for table detection.

    Attributes:
        min_confidence: Drop tables/cells below this confidence (0-1).
        detect_cells: Whether to build the per-cell grid (otherwise only the
            table bounding box is returned).
    """

    min_confidence: float = 0.0
    detect_cells: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")

    def keeps(self, confidence: float) -> bool:
        """Return True if a table/cell at *confidence* passes the filter."""
        return confidence >= self.min_confidence
