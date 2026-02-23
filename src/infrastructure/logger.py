"""
src/infrastructure/logger.py

Structured logging setup for the Stratego application.

Provides two public helpers:

* :func:`setup_logging` – Configure the root Stratego logger with a
  :class:`~logging.handlers.RotatingFileHandler` and (optionally) a
  :class:`~logging.StreamHandler` for console output.

* :func:`get_logger` – Return a named child logger beneath the ``stratego``
  root namespace.

Specification: system_design.md §2.5
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Root logger namespace for all stratego loggers.
_ROOT_LOGGER_NAME = "stratego"

# Default format includes timestamp, level, logger name, and message.
_LOG_FORMAT = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"

# Log file name and rotation settings.
_LOG_FILENAME = "stratego.log"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 3


def setup_logging(
    *,
    log_dir: Path,
    level: str = "INFO",
    console: bool = False,
) -> None:
    """Configure the application logger.

    Creates *log_dir* (including any missing parents) if it does not exist,
    then attaches a :class:`~logging.handlers.RotatingFileHandler` to the
    root ``stratego`` logger.

    Calling this function multiple times replaces any previously attached
    handlers, ensuring idempotent setup.

    Args:
        log_dir: Directory where the rotating log file is written.
        level: Minimum log level as a string (``"DEBUG"``, ``"INFO"``,
            ``"WARNING"``, ``"ERROR"``, or ``"CRITICAL"``).
        console: If ``True``, also attach a :class:`~logging.StreamHandler`
            that writes to ``stderr``.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / _LOG_FILENAME

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger(_ROOT_LOGGER_NAME)
    root.setLevel(numeric_level)

    # Remove all pre-existing handlers to avoid duplicates on repeated calls.
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    if console:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(numeric_level)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger beneath the ``stratego`` root namespace.

    Args:
        name: Module or component name (e.g. ``"game_controller"``).

    Returns:
        A :class:`logging.Logger` named ``stratego.<name>``.
    """
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
