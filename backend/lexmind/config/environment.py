"""Environment helpers."""

import os

from lexmind.config.config_types import Environment


def detect_environment() -> Environment:
    """Detect the active environment from LEXMIND_ENV or default."""
    raw = os.environ.get("LEXMIND_ENV", os.environ.get("ENV", "")).strip().lower()
    for env in Environment:
        if env.value == raw:
            return env
    return Environment.DEVELOPMENT


def is_production(env: Environment | None = None) -> bool:
    """Return True for the production environment."""
    return (env or detect_environment()) == Environment.PRODUCTION
