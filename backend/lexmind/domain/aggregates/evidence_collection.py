"""Evidence collection aggregate root."""

from dataclasses import dataclass, field

from lexmind.domain.entities.evidence import Evidence
from lexmind.domain.enums.domain_enums import EvidenceType
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class EvidenceCollection:
    """EvidenceCollection aggregate root.

    Manages a set of evidence items for a case, enforcing
    the rule that each evidence item must reference at least one document.
    """

    case_id: str = ""
    _evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    @property
    def count(self) -> int:
        """Return the number of evidence items."""
        return len(self._evidence)

    @property
    def evidence_ids(self) -> tuple[str, ...]:
        """Return all evidence IDs."""
        return tuple(e.id for e in self._evidence)

    def add(self, evidence: Evidence) -> None:
        """Add an evidence item to the collection.

        Raises:
            InvariantViolationError: If the evidence is already in the collection.
        """
        if any(e.id == evidence.id for e in self._evidence):
            raise InvariantViolationError(
                f"Evidence '{evidence.id}' already in collection"
            )
        evidence.link_to_case(self.case_id)
        self._evidence = (*self._evidence, evidence)

    def remove(self, evidence_id: str) -> None:
        """Remove an evidence item from the collection."""
        self._evidence = tuple(e for e in self._evidence if e.id != evidence_id)

    def get(self, evidence_id: str) -> Evidence | None:
        """Return an evidence item by ID, or None."""
        for e in self._evidence:
            if e.id == evidence_id:
                return e
        return None

    def by_type(self, evidence_type: EvidenceType) -> tuple[Evidence, ...]:
        """Return all evidence items of a given type."""
        return tuple(e for e in self._evidence if e.evidence_type == evidence_type)
