"""Language detector contract, registry and concrete detectors.

A :class:`LanguageDetector` identifies the natural language(s) present in a
piece of text.  The rule-based detector is a no-dependency default that
returns a single hardcoded language.  Model-backed detection is provided by
:class:`DetectionLanguageDetector`, which wraps an injected
:class:`LanguageDetectionEngine`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import structlog

from lexmind.language_detection.language_detection_types import (
    DetectedLanguage,
    LanguageDetectionOptions,
    LanguageDetectionResult,
)

logger = structlog.get_logger(__name__)


@runtime_checkable
class LanguageDetector(Protocol):
    """Detects the natural language(s) of text."""

    @property
    def name(self) -> str:
        """Return the unique detector name."""
        ...

    def detect(
        self,
        text: str,
        options: LanguageDetectionOptions | None = None,
    ) -> LanguageDetectionResult:
        """Detect languages in *text* and return the result."""
        ...


@runtime_checkable
class LanguageDetectionEngine(Protocol):
    """Low-level language detection engine (typically a trained model)."""

    def detect(
        self,
        text: str,
        options: LanguageDetectionOptions,
    ) -> tuple[DetectedLanguage, ...]:
        """Return raw detected languages for the given text."""
        ...


class LanguageDetectorNotFoundError(ValueError):
    """Raised when no detector is registered for a name."""


class RuleBasedLanguageDetector:
    """No-dependency default detector.

    Returns a single hardcoded language with full confidence.  Fully
    exercised by unit tests.
    """

    def __init__(self) -> None:
        """Initialise the rule-based detector."""

    @property
    def name(self) -> str:
        """Return the detector name."""
        return "rule-based"

    def detect(
        self,
        text: str,
        options: LanguageDetectionOptions | None = None,
    ) -> LanguageDetectionResult:
        """Return a single hardcoded ``"en"`` result.

        Raises:
            ValueError: If *text* is empty.
        """
        if not text:
            raise ValueError("text must not be empty")
        lang = DetectedLanguage(code="en", confidence=1.0)
        logger.info("language_rule_based", detector=self.name)
        return LanguageDetectionResult(
            text_or_page="",
            languages=(lang,),
            detector=self.name,
        )


class DetectionLanguageDetector:
    """Detector backed by an injected language detection engine."""

    def __init__(
        self,
        engine: LanguageDetectionEngine,
        name: str = "detection",
    ) -> None:
        """Initialise with a detection engine.

        Raises:
            ValueError: If *engine* is ``None``.
        """
        if engine is None:
            raise ValueError("engine must not be None")
        self._engine = engine
        self._name = name

    @property
    def name(self) -> str:
        """Return the detector name."""
        return self._name

    def detect(
        self,
        text: str,
        options: LanguageDetectionOptions | None = None,
    ) -> LanguageDetectionResult:
        """Run the detection engine and filter results by *options*.

        Raises:
            ValueError: If *text* is empty.
        """
        if not text:
            raise ValueError("text must not be empty")
        options = options or LanguageDetectionOptions()
        raw = self._engine.detect(text, options)
        filtered = tuple(lang for lang in raw if options.keeps(lang))
        logger.info(
            "language_detection",
            detector=self._name,
            languages=len(filtered),
        )
        return LanguageDetectionResult(
            text_or_page="",
            languages=filtered,
            detector=self._name,
        )


class LanguageDetectorRegistry:
    """Registry mapping detector names to :class:`LanguageDetector` instances."""

    def __init__(self) -> None:
        self._detectors: dict[str, LanguageDetector] = {}

    def register(self, detector: LanguageDetector) -> None:
        """Register a detector under its ``name``.

        Raises:
            ValueError: If the detector name is empty.
        """
        if not detector.name:
            raise ValueError("detector name must not be empty")
        self._detectors[detector.name] = detector

    def get(self, name: str) -> LanguageDetector:
        """Return the detector registered under *name*.

        Raises:
            LanguageDetectorNotFoundError: If no detector is registered.
        """
        detector = self._detectors.get(name)
        if detector is None:
            raise LanguageDetectorNotFoundError(
                f"No language detector registered under '{name}'"
            )
        return detector

    def has(self, name: str) -> bool:
        """Return True if a detector is registered under *name*."""
        return name in self._detectors

    def registered_names(self) -> list[str]:
        """Return the registered detector names."""
        return sorted(self._detectors)
