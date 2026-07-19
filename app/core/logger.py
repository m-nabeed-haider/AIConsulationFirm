"""Centralized logging configuration.

This module configures a single Loguru logger instance used across
the entire application. It sets up two sinks:

* A console sink with a human-readable, colorized format.
* A rotating file sink under the ``logs/`` directory for persistent
  records.

Other modules should import the shared ``logger`` object directly::

    from app.core.logger import logger

    logger.info("Something happened")
"""

import sys
from pathlib import Path

from loguru import logger

from app.core.config import get_settings
from app.core.constants import (LOG_DIRECTORY_NAME, LOG_FILE_NAME,
                                LOG_RETENTION_PERIOD, LOG_ROTATION_SIZE)

_CONSOLE_FORMAT: str = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

_FILE_FORMAT: str = (
    "{time:YYYY-MM-DD HH:mm:ss} | "
    "{level: <8} | "
    "{name}:{function}:{line} - "
    "{message}"
)

_is_configured: bool = False


def _resolve_log_directory() -> Path:
    """Resolve the absolute path to the application's log directory.

    Returns:
        Path: Path to the ``logs/`` directory at the project root,
        creating it if it does not already exist.
    """
    project_root = Path(__file__).resolve().parents[2]
    log_directory = project_root / LOG_DIRECTORY_NAME
    log_directory.mkdir(parents=True, exist_ok=True)
    return log_directory


def configure_logging() -> None:
    """Configure the shared Loguru logger with console and file sinks.

    This function is idempotent: calling it multiple times will not
    duplicate sinks. It reads the desired log level from the
    application settings.
    """
    global _is_configured

    if _is_configured:
        return

    settings = get_settings()
    log_directory = _resolve_log_directory()
    log_file_path = log_directory / LOG_FILE_NAME

    logger.remove()

    logger.add(
        sys.stdout,
        level=settings.log_level,
        format=_CONSOLE_FORMAT,
        colorize=True,
        backtrace=False,
        diagnose=False,
    )

    logger.add(
        log_file_path,
        level=settings.log_level,
        format=_FILE_FORMAT,
        rotation=LOG_ROTATION_SIZE,
        retention=LOG_RETENTION_PERIOD,
        encoding="utf-8",
        backtrace=False,
        diagnose=False,
    )

    _is_configured = True


__all__ = ["logger", "configure_logging"]
