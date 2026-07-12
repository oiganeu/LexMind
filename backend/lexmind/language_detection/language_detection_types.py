"""Language detection value objects.

Language detection identifies the natural language(s) present in a piece of
text.  A :class:`DetectedLanguage` carries an ISO-639 code and a confidence
score; a :class:`LanguageDetectionOptions` controls filtering; and a
:class:`LanguageDetectionResult` bundles the detected languages together with
a reference to the source text.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class DetectedLanguage:
    """A single detected language with confidence.

    Attributes:
        code: ISO-639 language code (e.g. ``"en"``, ``"ro"``).
        confidence: Detection confidence in [0, 1].
    """

    code: str
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("code must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class LanguageDetectionOptions:
    """Declarative request for language detection.

    Attributes:
        candidate_codes: If non-empty, only languages whose code is in this
            set are kept.
        min_confidence: Languages below this confidence are dropped.
    """

    candidate_codes: tuple[str, ...] = ()
    min_confidence: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")

    def keeps(self, lang: DetectedLanguage) -> bool:
        """Return True if *lang* passes both filters."""
        if lang.confidence < self.min_confidence:
            return False
        return not self.candidate_codes or lang.code in self.candidate_codes


@dataclass(frozen=True, slots=True)
class LanguageDetectionResult:
    """Outcome of a language detection run.

    Attributes:
        text_or_page: Reference to the source text or page identifier.
        languages: Detected languages ordered by relevance.
        detector: Name of the detector that produced this result.
    """

    text_or_page: str
    languages: tuple[DetectedLanguage, ...] = field(default_factory=tuple)
    detector: str = ""

    @property
    def top_language(self) -> DetectedLanguage | None:
        """Return the highest-confidence language or ``None``."""
        if not self.languages:
            return None
        return max(self.languages, key=lambda lang: lang.confidence)

    @property
    def is_empty(self) -> bool:
        """Return True if no languages were detected."""
        return not self.languages
