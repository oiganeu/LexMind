"""Unit tests for domain value objects."""

from decimal import Decimal

import pytest

from lexmind.domain.exceptions.domain_exceptions import InvariantViolationError
from lexmind.domain.value_objects.address import Address
from lexmind.domain.value_objects.citation import Citation
from lexmind.domain.value_objects.confidence import ConfidenceScore
from lexmind.domain.value_objects.contact import EmailAddress, PhoneNumber
from lexmind.domain.value_objects.date_range import DateRange
from lexmind.domain.value_objects.document import DocumentTitle
from lexmind.domain.value_objects.file import FileHash, FilePath
from lexmind.domain.value_objects.geometry import Coordinate, PageNumber
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


class TestIdentifier:
    def test_valid_identifier(self) -> None:
        ident = Identifier(value="abc-123")
        assert ident.value == "abc-123"

    def test_empty_identifier_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Identifier(value="")

    def test_whitespace_identifier_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Identifier(value="   ")

    def test_equality(self) -> None:
        assert Identifier(value="x") == Identifier(value="x")
        assert Identifier(value="x") != Identifier(value="y")

    def test_hash(self) -> None:
        assert hash(Identifier(value="x")) == hash(Identifier(value="x"))


class TestTypedIds:
    def test_workspace_id(self) -> None:
        wid = WorkspaceId(value="w-1")
        assert wid.value == "w-1"
        assert isinstance(wid, Identifier)

    def test_case_id(self) -> None:
        cid = CaseId(value="c-1")
        assert cid.value == "c-1"

    def test_document_id(self) -> None:
        did = DocumentId(value="d-1")
        assert did.value == "d-1"

    def test_evidence_id(self) -> None:
        eid = EvidenceId(value="e-1")
        assert eid.value == "e-1"


class TestFileHash:
    def test_valid_hash(self) -> None:
        h = FileHash(value="a" * 40)
        assert h.value == "a" * 40

    def test_invalid_length_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            FileHash(value="abc")

    def test_invalid_chars_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            FileHash(value="g" * 40)


class TestFilePath:
    def test_valid_path(self) -> None:
        fp = FilePath(value="docs/file.pdf")
        assert fp.value == "docs/file.pdf"

    def test_absolute_path_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            FilePath(value="/etc/passwd")

    def test_dotdot_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            FilePath(value="../etc/passwd")

    def test_empty_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            FilePath(value="")


class TestDateRange:
    def test_valid_range(self) -> None:
        from datetime import date

        dr = DateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))
        assert dr.duration_days == 364

    def test_inverted_range_raises(self) -> None:
        from datetime import date

        with pytest.raises(InvariantViolationError):
            DateRange(start=date(2025, 12, 31), end=date(2025, 1, 1))

    def test_contains(self) -> None:
        from datetime import date

        dr = DateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))
        assert dr.contains(date(2025, 6, 15))
        assert not dr.contains(date(2026, 1, 1))

    def test_overlaps(self) -> None:
        from datetime import date

        dr1 = DateRange(start=date(2025, 1, 1), end=date(2025, 6, 30))
        dr2 = DateRange(start=date(2025, 3, 1), end=date(2025, 12, 31))
        assert dr1.overlaps(dr2)

    def test_no_overlap(self) -> None:
        from datetime import date

        dr1 = DateRange(start=date(2025, 1, 1), end=date(2025, 3, 31))
        dr2 = DateRange(start=date(2025, 6, 1), end=date(2025, 12, 31))
        assert not dr1.overlaps(dr2)


class TestDocumentTitle:
    def test_valid_title(self) -> None:
        t = DocumentTitle(value="Contract No. 123")
        assert t.value == "Contract No. 123"

    def test_empty_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            DocumentTitle(value="")

    def test_too_long_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            DocumentTitle(value="x" * 501)

    def test_normalized(self) -> None:
        t = DocumentTitle(value="  Contract   No.   123  ")
        assert t.normalized == "Contract No. 123"


class TestLanguage:
    def test_valid_language(self) -> None:
        lang = Language(value="ro")
        assert lang.value == "ro"

    def test_invalid_length_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Language(value="ron")

    def test_uppercase_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Language(value="EN")


class TestCoordinate:
    def test_valid(self) -> None:
        c = Coordinate(latitude=44.4268, longitude=26.1025)
        assert c.latitude == 44.4268

    def test_invalid_latitude(self) -> None:
        with pytest.raises(InvariantViolationError):
            Coordinate(latitude=91.0, longitude=0.0)

    def test_invalid_longitude(self) -> None:
        with pytest.raises(InvariantViolationError):
            Coordinate(latitude=0.0, longitude=181.0)


class TestPageNumber:
    def test_valid(self) -> None:
        p = PageNumber(value=1)
        assert p.value == 1

    def test_zero_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            PageNumber(value=0)


class TestConfidenceScore:
    def test_valid(self) -> None:
        c = ConfidenceScore(value=0.75)
        assert c.percentage == 75.0

    def test_boundary_zero(self) -> None:
        c = ConfidenceScore(value=0.0)
        assert c.percentage == 0.0

    def test_boundary_one(self) -> None:
        c = ConfidenceScore(value=1.0)
        assert c.percentage == 100.0

    def test_out_of_range_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            ConfidenceScore(value=1.5)


class TestVersion:
    def test_valid_semver(self) -> None:
        v = Version(value="1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3

    def test_invalid_semver_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Version(value="not-a-version")

    def test_next_major(self) -> None:
        v = Version(value="1.2.3")
        assert v.next_major().value == "2.0.0"

    def test_next_minor(self) -> None:
        v = Version(value="1.2.3")
        assert v.next_minor().value == "1.3.0"

    def test_next_patch(self) -> None:
        v = Version(value="1.2.3")
        assert v.next_patch().value == "1.2.4"


class TestCitation:
    def test_valid(self) -> None:
        c = Citation(value="Legea nr. 286/2009")
        assert c.value == "Legea nr. 286/2009"

    def test_empty_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Citation(value="")


class TestEmailAddress:
    def test_valid(self) -> None:
        e = EmailAddress(value="user@example.com")
        assert e.value == "user@example.com"

    def test_invalid_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            EmailAddress(value="not-an-email")


class TestPhoneNumber:
    def test_valid(self) -> None:
        p = PhoneNumber(value="+40722123456")
        assert p.value == "+40722123456"

    def test_invalid_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            PhoneNumber(value="abc")


class TestMoney:
    def test_valid(self) -> None:
        m = Money(amount=Decimal("100.50"), currency="RON")
        assert m.amount == Decimal("100.50")

    def test_negative_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Money(amount=Decimal("-1"), currency="RON")

    def test_add(self) -> None:
        m1 = Money(amount=Decimal("10"), currency="EUR")
        m2 = Money(amount=Decimal("20"), currency="EUR")
        result = m1 + m2
        assert result.amount == Decimal("30")

    def test_add_different_currency_raises(self) -> None:
        m1 = Money(amount=Decimal("10"), currency="EUR")
        m2 = Money(amount=Decimal("20"), currency="RON")
        with pytest.raises(InvariantViolationError):
            m1 + m2

    def test_mul(self) -> None:
        m = Money(amount=Decimal("10"), currency="RON")
        result = m * 3
        assert result.amount == Decimal("30")


class TestAddress:
    def test_valid(self) -> None:
        a = Address(street="Strada Linistei 1", city="Bucuresti")
        assert "Strada Linistei 1" in a.one_line

    def test_empty_street_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Address(street="", city="Bucuresti")

    def test_empty_city_raises(self) -> None:
        with pytest.raises(InvariantViolationError):
            Address(street="Strada Linistei 1", city="")


class TestTagSet:
    def test_empty(self) -> None:
        ts = TagSet()
        assert len(ts) == 0

    def test_add(self) -> None:
        ts = TagSet(tags=["urgent"])
        assert "urgent" in ts

    def test_deduplication(self) -> None:
        ts = TagSet(tags=["urgent", "Urgent", "URGENT"])
        assert len(ts) == 1

    def test_sorted(self) -> None:
        ts = TagSet(tags=["c", "a", "b"])
        assert list(ts) == ["a", "b", "c"]

    def test_remove(self) -> None:
        ts = TagSet(tags=["a", "b"])
        ts2 = ts.remove("a")
        assert "a" not in ts2
        assert "b" in ts2

    def test_union(self) -> None:
        ts1 = TagSet(tags=["a", "b"])
        ts2 = TagSet(tags=["b", "c"])
        ts3 = ts1.union(ts2)
        assert len(ts3) == 3

    def test_is_subset(self) -> None:
        ts1 = TagSet(tags=["a"])
        ts2 = TagSet(tags=["a", "b"])
        assert ts1.is_subset(ts2)
        assert not ts2.is_subset(ts1)

    def test_immutability(self) -> None:
        ts = TagSet(tags=["a"])
        ts2 = ts.add("b")
        assert len(ts) == 1
        assert len(ts2) == 2


class TestValueObjectBase:
    def test_frozen(self) -> None:
        vo = Identifier(value="test")
        with pytest.raises(AttributeError):
            vo.value = "changed"  # type: ignore[misc]

    def test_replace(self) -> None:
        vo = Identifier(value="old")
        vo2 = vo.replace(value="new")
        assert vo.value == "old"
        assert vo2.value == "new"
