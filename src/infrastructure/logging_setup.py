"""Centralized loguru configuration.

Log messages are in English (for developers), per project brief §2.4;
user-facing Arabic messages are a presentation-layer concern.
"""

import sys

from loguru import logger


def configure_logging(level: str = "INFO") -> None:
    """Configure loguru to log to stderr with a compact format.

    In a PyInstaller `--windowed` build there is no console, so
    `sys.stderr` is `None`; adding a sink there would make every log
    call raise (loguru's own error-reporting path writes to
    `sys.stderr` too, so the exception isn't even caught) and take
    down whichever API method happened to log first. Skip the sink
    entirely in that case — the in-app log panel (a separate sink
    added by `MainApi.bind_window`) is still fully functional.
    """
    logger.remove()
    if sys.stderr is None:
        return
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )
