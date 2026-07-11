"""Tesseract OCR configuration.

Immutable configuration object injected into the Tesseract provider.
Kept engine-agnostic in shape so sibling providers (PaddleOCR, EasyOCR)
can follow the same pattern.
"""

from __future__ import annotations

from dataclasses import dataclass

_MIN_PSM = 0
_MAX_PSM = 13
_MIN_OEM = 0
_MAX_OEM = 3


@dataclass(frozen=True, slots=True)
class TesseractConfig:
    """Configuration for the Tesseract engine.

    Attributes:
        language: Default language code (e.g. ``eng``, ``ron``).
        psm: Page segmentation mode (0-13).
        oem: OCR engine mode (0-3).
        extra_config: Additional raw Tesseract config flags.
        timeout: Recognition timeout in seconds (0 = no timeout).
        min_confidence: Minimum per-word confidence (0-100) to keep.
    """

    language: str = "eng"
    psm: int = 3
    oem: int = 3
    extra_config: str = ""
    timeout: float = 0.0
    min_confidence: float = 0.0

    def __post_init__(self) -> None:
        if not self.language:
            raise ValueError("language is required")
        if not _MIN_PSM <= self.psm <= _MAX_PSM:
            raise ValueError(f"psm must be between {_MIN_PSM} and {_MAX_PSM}")
        if not _MIN_OEM <= self.oem <= _MAX_OEM:
            raise ValueError(f"oem must be between {_MIN_OEM} and {_MAX_OEM}")
        if self.timeout < 0:
            raise ValueError("timeout must be non-negative")
        if not 0.0 <= self.min_confidence <= 100.0:
            raise ValueError("min_confidence must be between 0 and 100")

    def to_config_string(self) -> str:
        """Return the Tesseract ``config`` string for CLI/API use."""
        parts = [f"--psm {self.psm}", f"--oem {self.oem}"]
        if self.extra_config:
            parts.append(self.extra_config)
        return " ".join(parts)

    def with_language(self, language: str) -> TesseractConfig:
        """Return a copy of this config using *language* if provided."""
        if not language or language == self.language:
            return self
        return TesseractConfig(
            language=language,
            psm=self.psm,
            oem=self.oem,
            extra_config=self.extra_config,
            timeout=self.timeout,
            min_confidence=self.min_confidence,
        )
