"""Application lifecycle hooks."""

from lexmind.logging import get_logger

logger = get_logger("lifecycle")


def startup() -> None:
    """Run startup procedures (no services yet)."""
    logger.info("lexmind.startup")


def shutdown() -> None:
    """Run shutdown procedures (no services yet)."""
    logger.info("lexmind.shutdown")
