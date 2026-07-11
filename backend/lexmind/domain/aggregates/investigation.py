"""Investigation aggregate root."""

from dataclasses import dataclass, field

from lexmind.domain.entities.finding import Finding
from lexmind.domain.entities.investigation import Investigation
from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError


@dataclass
class InvestigationAggregate:
    """Investigation aggregate root.

    Manages an investigation and its findings, enforcing
    the rule that an investigation must have findings before completion.
    """

    investigation: Investigation = field(default_factory=Investigation)
    _findings: tuple[Finding, ...] = field(default_factory=tuple)

    @property
    def id(self) -> str:
        """Return the investigation ID."""
        return self.investigation.id

    @property
    def title(self) -> str:
        """Return the investigation title."""
        return self.investigation.title

    @property
    def is_completed(self) -> bool:
        """Return True if the investigation is completed."""
        return self.investigation.is_completed

    @property
    def finding_count(self) -> int:
        """Return the number of findings."""
        return len(self._findings)

    def add_finding(self, finding: Finding) -> None:
        """Add a finding to the investigation.

        Raises:
            InvariantViolationError: If the finding already exists.
        """
        if any(f.id == finding.id for f in self._findings):
            raise InvariantViolationError(
                f"Finding '{finding.id}' already in investigation"
            )
        self._findings = (*self._findings, finding)
        self.investigation.add_finding(finding.id)

    def add_document(self, document_id: str) -> None:
        """Link a document to the investigation."""
        self.investigation.add_document(document_id)

    def complete(self) -> None:
        """Mark the investigation as completed.

        Raises:
            InvariantViolationError: If there are no findings.
        """
        if not self._findings:
            raise InvariantViolationError(
                "Cannot complete an investigation with no findings"
            )
        self.investigation.complete()
