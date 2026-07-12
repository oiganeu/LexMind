"""OCR quality metric calculators and registry.

A :class:`QualityMetricCalculator` turns OCR text (and an optional reference)
into a single :class:`~lexmind.ocr.quality.quality_types.QualityMetric`.
Calculators are registered in a :class:`QualityCalculatorRegistry` so the
service can run them composably.  The bundled calculators are dependency-free
and heuristic: they estimate quality from text composition rather than from a
real OCR engine confidence channel.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lexmind.ocr.quality.quality_types import (
    OcrQualityOptions,
    QualityMetric,
)


class QualityCalculatorNotFoundError(ValueError):
    """Raised when no calculator is registered for a name."""


@runtime_checkable
class QualityMetricCalculator(Protocol):
    """Computes a single quality metric from OCR output."""

    @property
    def name(self) -> str:
        """Return the unique calculator name."""
        ...

    def calculate(
        self,
        ocr_text: str,
        reference: str | None = None,
        options: OcrQualityOptions | None = None,
    ) -> QualityMetric:
        """Return a :class:`QualityMetric` for *ocr_text*."""
        ...


@runtime_checkable
class OcrQualityEngine(Protocol):
    """Optional aggregation hook computing the overall score."""

    def aggregate(
        self,
        metrics: list[QualityMetric],
        options: OcrQualityOptions,
    ) -> float:
        """Return the overall score in ``[0, 1]`` for *metrics*."""
        ...


class ConfidenceMetricCalculator:
    """Rule-based confidence estimate from character composition.

    The share of non-whitespace characters that are alphanumeric is used as a
    confidence proxy: letters and digits are reliably recognised while stray
    symbols are a frequent OCR artefact.  Empty output scores 0.0.
    """

    def __init__(self, name: str = "confidence") -> None:
        """Initialise the calculator with a metric name."""
        self._name = name

    @property
    def name(self) -> str:
        """Return the calculator name."""
        return self._name

    def calculate(
        self,
        ocr_text: str,
        reference: str | None = None,
        options: OcrQualityOptions | None = None,
    ) -> QualityMetric:
        """Estimate a confidence proxy in ``[0, 1]`` for *ocr_text*."""
        if not ocr_text:
            return QualityMetric(
                name=self._name,
                score=0.0,
                weight=1.0,
                details={"reason": "empty", "reference_provided": reference is not None},
            )
        non_ws = [char for char in ocr_text if not char.isspace()]
        if not non_ws:
            return QualityMetric(
                name=self._name,
                score=0.0,
                weight=1.0,
                details={"reason": "whitespace_only", "length": len(ocr_text)},
            )
        alnum = sum(1 for char in non_ws if char.isalnum())
        score = alnum / len(non_ws)
        return QualityMetric(
            name=self._name,
            score=score,
            weight=1.0,
            details={"alnum": alnum, "non_whitespace": len(non_ws)},
        )


class LengthMetricCalculator:
    """Rule-based length heuristic.

    Very short OCR output is suspicious (a page that was not really read).
    The score scales linearly from 0 at empty text to 1.0 at or above an
    expected length, which defaults to a single page of body text.
    """

    def __init__(
        self,
        name: str = "length",
        expected_length: int = 200,
    ) -> None:
        """Initialise with *expected_length* (score saturates there)."""
        if expected_length <= 0:
            raise ValueError("expected_length must be positive")
        self._name = name
        self._expected_length = expected_length

    @property
    def name(self) -> str:
        """Return the calculator name."""
        return self._name

    def calculate(
        self,
        ocr_text: str,
        reference: str | None = None,
        options: OcrQualityOptions | None = None,
    ) -> QualityMetric:
        """Score *ocr_text* by length relative to the expected length."""
        length = len(ocr_text)
        if length <= 0:
            score = 0.0
        elif length >= self._expected_length:
            score = 1.0
        else:
            score = length / self._expected_length
        return QualityMetric(
            name=self._name,
            score=score,
            weight=1.0,
            details={"length": length, "expected": self._expected_length},
        )


class WhitespaceMetricCalculator:
    """Rule-based whitespace balance heuristic.

    A high ratio of whitespace to total characters suggests broken layout or
    missed text.  The score is 1.0 up to a tolerated ratio and then decays
    linearly to 0.0 at all-whitespace text.
    """

    def __init__(
        self,
        name: str = "whitespace",
        max_whitespace_ratio: float = 0.6,
    ) -> None:
        """Initialise with the tolerated whitespace *max_whitespace_ratio*."""
        if not 0.0 <= max_whitespace_ratio <= 1.0:
            raise ValueError("max_whitespace_ratio must be between 0 and 1")
        self._name = name
        self._max_ratio = max_whitespace_ratio

    @property
    def name(self) -> str:
        """Return the calculator name."""
        return self._name

    def calculate(
        self,
        ocr_text: str,
        reference: str | None = None,
        options: OcrQualityOptions | None = None,
    ) -> QualityMetric:
        """Score *ocr_text* by whitespace balance."""
        total = len(ocr_text)
        if total == 0:
            return QualityMetric(
                name=self._name,
                score=0.0,
                weight=1.0,
                details={"reason": "empty"},
            )
        whitespace = sum(1 for char in ocr_text if char.isspace())
        ratio = whitespace / total
        if ratio <= self._max_ratio:
            score = 1.0
        else:
            excess = ratio - self._max_ratio
            span = max(1e-9, 1.0 - self._max_ratio)
            score = max(0.0, 1.0 - excess / span)
        return QualityMetric(
            name=self._name,
            score=score,
            weight=1.0,
            details={"whitespace_ratio": ratio, "max_ratio": self._max_ratio},
        )


class QualityCalculatorRegistry:
    """Registry mapping calculator names to :class:`QualityMetricCalculator`."""

    def __init__(self) -> None:
        self._calculators: dict[str, QualityMetricCalculator] = {}

    def register(self, calculator: QualityMetricCalculator) -> None:
        """Register *calculator* under its ``name``.

        Raises:
            ValueError: If the calculator name is empty.
        """
        if not calculator.name:
            raise ValueError("calculator name must not be empty")
        self._calculators[calculator.name] = calculator

    def get(self, name: str) -> QualityMetricCalculator:
        """Return the calculator registered under *name*.

        Raises:
            QualityCalculatorNotFoundError: If no calculator is registered.
        """
        calculator = self._calculators.get(name)
        if calculator is None:
            raise QualityCalculatorNotFoundError(
                f"No quality calculator registered under '{name}'"
            )
        return calculator

    def has(self, name: str) -> bool:
        """Return True if a calculator is registered under *name*."""
        return name in self._calculators

    def registered_names(self) -> list[str]:
        """Return the registered calculator names in sorted order."""
        return sorted(self._calculators)
