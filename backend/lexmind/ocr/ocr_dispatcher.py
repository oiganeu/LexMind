"""OCR dispatcher -- selects an OCR provider.

Maintains a registry of available :class:`OCRProvider` plugins and
chooses the appropriate one for a given request.  Provider selection is
fully dependency-injected: providers are registered at composition time.
"""

from __future__ import annotations

import structlog

from lexmind.ocr.ocr_provider import OCRProvider

logger = structlog.get_logger(__name__)


class OCRProviderNotFoundError(Exception):
    """Raised when no suitable OCR provider can be selected."""

    def __init__(self, detail: str) -> None:
        """Initialise with a human-readable detail message."""
        super().__init__(detail)
        self.detail = detail


class OCRDispatcher:
    """Selects OCR providers from a registry.

    Providers are registered by name.  A default provider may be
    designated for use when no explicit provider is requested.
    """

    def __init__(self, default_provider: str | None = None) -> None:
        """Initialise an empty dispatcher.

        Args:
            default_provider: Optional name of the provider to use when
                no explicit name is given to :meth:`select`.
        """
        self._providers: dict[str, OCRProvider] = {}
        self._default = default_provider

    def register(self, provider: OCRProvider) -> None:
        """Register an OCR provider under its ``name``.

        Args:
            provider: The provider to register.
        """
        self._providers[provider.name] = provider
        if self._default is None:
            self._default = provider.name
        logger.info("ocr_provider_registered", provider=provider.name)

    def unregister(self, name: str) -> None:
        """Remove a registered provider by name."""
        self._providers.pop(name, None)
        if self._default == name:
            self._default = next(iter(self._providers), None)

    def has_provider(self, name: str) -> bool:
        """Return True if a provider with *name* is registered."""
        return name in self._providers

    @property
    def default_provider(self) -> str | None:
        """Return the name of the default provider, if any."""
        return self._default

    def select(
        self,
        name: str | None = None,
        mime_type: str = "",
    ) -> OCRProvider:
        """Select a provider by name, or the default, or by MIME support.

        Selection order:
            1. Explicit *name* if provided.
            2. The configured default provider.
            3. The first registered provider that supports *mime_type*.

        Args:
            name: Explicit provider name to select.
            mime_type: MIME type used for capability-based fallback.

        Returns:
            The selected provider.

        Raises:
            OCRProviderNotFoundError: If no provider can be selected.
        """
        if name is not None:
            provider = self._providers.get(name)
            if provider is None:
                raise OCRProviderNotFoundError(
                    f"No OCR provider registered under name={name!r}"
                )
            return provider

        if self._default is not None:
            default = self._providers.get(self._default)
            if default is not None and (
                not mime_type or default.supports(mime_type)
            ):
                return default

        if mime_type:
            for provider in self._providers.values():
                if provider.supports(mime_type):
                    return provider

        raise OCRProviderNotFoundError(
            f"No OCR provider available for mime_type={mime_type!r}"
        )

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"OCRDispatcher(providers={list(self._providers.keys())})"
