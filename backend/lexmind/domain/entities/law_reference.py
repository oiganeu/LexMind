"""Law reference entity."""

from dataclasses import dataclass

from lexmind.domain.entities.base import BaseEntity
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class LawReference(BaseEntity):
    """LawReference — a specific law, regulation, or legal act."""

    title: str = ""
    official_number: str = ""
    year: int | None = None
    country: str = ""
    effective_date: str | None = None
    is_amended: bool = False
    citation_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise InvariantViolationError("LawReference title must not be empty")
