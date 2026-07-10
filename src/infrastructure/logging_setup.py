"""Centralized loguru configuration.

Log messages are in English (for developers), per project brief §2.4;
user-facing Arabic messages are a presentation-layer concern.
"""

import sys

from loguru import logger


def configure_logging(level: str = "INFO") -> None:
    """Configure loguru to log to stderr with a compact format."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )
