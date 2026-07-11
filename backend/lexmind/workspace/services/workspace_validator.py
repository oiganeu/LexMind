"""Workspace Validator -- validates workspace properties and constraints.

Responsibilities:
    - Validate workspace name (non-empty, valid characters)
    - Check name uniqueness via repository
    - No persistence, no events
"""

from __future__ import annotations

import re

from lexmind.workspace.workspace_exceptions import WorkspaceValidationError

_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\- ]+$")
_MAX_NAME_LENGTH = 255


class WorkspaceValidator:
    """Validates workspace properties before persistence.

    Stateless service -- all methods are pure functions.
    """

    def __init__(self, workspace_repository: object | None = None) -> None:
        """Initialise with an optional workspace repository.

        Args:
            workspace_repository: Used for uniqueness checks.  If None,
                uniqueness validation is skipped.
        """
        self._repo = workspace_repository

    def validate_name(self, name: str) -> None:
        """Validate that a workspace name meets all constraints.

        Args:
            name: The proposed workspace name.

        Raises:
            WorkspaceValidationError: If the name is invalid.
        """
        errors: list[str] = []

        if not name or not name.strip():
            errors.append("Workspace name must not be empty")
        elif len(name) > _MAX_NAME_LENGTH:
            errors.append(
                f"Workspace name must not exceed {_MAX_NAME_LENGTH} characters"
            )
        elif not _NAME_PATTERN.match(name.strip()):
            errors.append(
                "Workspace name may only contain letters, digits, "
                "hyphens, underscores, and spaces"
            )

        if errors:
            raise WorkspaceValidationError("; ".join(errors))

    def validate_uniqueness(self, name: str) -> None:
        """Check that the name is not already taken.

        Args:
            name: The proposed workspace name.

        Raises:
            WorkspaceValidationError: If the name already exists.
        """
        if self._repo is None:
            return

        existing = self._repo.get_by_name(name)  # type: ignore[union-attr]
        if existing is not None:
            raise WorkspaceValidationError(
                f"A workspace named '{name}' already exists"
            )

    def validate_all(self, name: str) -> None:
        """Run all validations on the given name.

        Args:
            name: The proposed workspace name.

        Raises:
            WorkspaceValidationError: On any validation failure.
        """
        self.validate_name(name)
        self.validate_uniqueness(name)
