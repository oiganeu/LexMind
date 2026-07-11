"""Dependency injection container.

Structure only — no implementations yet.
"""

from lexmind.settings import Settings, get_settings


def get_app_settings() -> Settings:
    """Return application settings (FastAPI dependency)."""
    return get_settings()
