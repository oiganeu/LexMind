"""Domain value objects — immutable, self-validating building blocks."""

from lexmind.domain.value_objects.address import Address
from lexmind.domain.value_objects.base import ValueObject
from lexmind.domain.value_objects.citation import Citation
from lexmind.domain.value_objects.confidence import ConfidenceScore
from lexmind.domain.value_objects.contact import EmailAddress, PhoneNumber
from lexmind.domain.value_objects.date_range import DateRange
from lexmind.domain.value_objects.document import DocumentTitle
from lexmind.domain.value_objects.file import FileHash, FilePath
from lexmind.domain.value_objects.geometry import Coordinate, GeoLocation, PageNumber
from lexmind.domain.value_objects.identifiers import (
    CaseId,
    DocumentId,
    EvidenceId,
    Identifier,
    WorkspaceId,
)
from lexmind.domain.value_objects.language import Language
from lexmind.domain.value_objects.money import Money
from lexmind.domain.value_objects.tags import TagSet
from lexmind.domain.value_objects.version import Version

__all__ = [
    "Address",
    "CaseId",
    "Citation",
    "ConfidenceScore",
    "Coordinate",
    "DateRange",
    "DocumentId",
    "DocumentTitle",
    "EmailAddress",
    "EvidenceId",
    "FilePath",
    "FileHash",
    "GeoLocation",
    "Identifier",
    "Language",
    "Money",
    "PageNumber",
    "PhoneNumber",
    "TagSet",
    "ValueObject",
    "Version",
    "WorkspaceId",
]
