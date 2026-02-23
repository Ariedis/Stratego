"""
test_logger.py — Unit tests for src/infrastructure/logger.py

Epic: EPIC-6 | User Story: US-603
Covers acceptance criteria: AC-1 through AC-4
Specification: system_design.md §2.5
"""
from __future__ import annotations

import logging
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.infrastructure.logger import get_logger, setup_logging

    _LOGGER_AVAILABLE = True
except ImportError:
    _LOGGER_AVAILABLE = False
    get_logger = None  # type: ignore[assignment, misc]
    setup_logging = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    not _LOGGER_AVAILABLE,
    reason="src.infrastructure.logger not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def log_dir(tmp_path: Path) -> Path:
    """Temporary log directory."""
    d = tmp_path / "logs"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# US-603 AC-1: error() with exc_info includes stack trace
# ---------------------------------------------------------------------------


class TestLoggerErrorWithStackTrace:
    """AC-1: logger.error() with exc_info=True includes timestamp, level, and trace."""

    def test_error_with_exc_info_captured(
        self, log_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-1: error log with exc_info must appear in caplog with ERROR level."""
        setup_logging(log_dir=log_dir, level="DEBUG")  # type: ignore[misc]
        logger = get_logger("test_module")  # type: ignore[misc]
        with caplog.at_level(logging.ERROR, logger="test_module"):
            try:
                raise ValueError("test error")
            except ValueError:
                logger.error("Invalid move", exc_info=True)
        assert any("Invalid move" in r.message for r in caplog.records)
        assert any(r.levelname == "ERROR" for r in caplog.records)

    def test_error_record_has_module_name(
        self, log_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-1: Log record must include the module name."""
        setup_logging(log_dir=log_dir, level="DEBUG")  # type: ignore[misc]
        logger = get_logger("game_controller")  # type: ignore[misc]
        with caplog.at_level(logging.ERROR, logger="game_controller"):
            logger.error("Test entry")
        assert any("game_controller" in r.name for r in caplog.records)


# ---------------------------------------------------------------------------
# US-603 AC-2: Level filtering
# ---------------------------------------------------------------------------


class TestLoggerLevelFiltering:
    """AC-2: Messages below the configured level must not be written."""

    def test_info_not_logged_at_warning_level(
        self, log_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-2: info() messages must not appear when level is WARNING."""
        setup_logging(log_dir=log_dir, level="WARNING")  # type: ignore[misc]
        logger = get_logger("filter_test")  # type: ignore[misc]
        with caplog.at_level(logging.WARNING, logger="filter_test"):
            logger.info("This should not appear")
        info_records = [r for r in caplog.records if r.levelname == "INFO"]
        assert len(info_records) == 0

    def test_warning_logged_at_warning_level(
        self, log_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC-2: warning() messages must appear when level is WARNING."""
        setup_logging(log_dir=log_dir, level="WARNING")  # type: ignore[misc]
        logger = get_logger("filter_test2")  # type: ignore[misc]
        with caplog.at_level(logging.WARNING, logger="filter_test2"):
            logger.warning("This should appear")
        assert any("This should appear" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# US-603 AC-3: Log file rotation
# ---------------------------------------------------------------------------


class TestLoggerFileRotation:
    """AC-3: RotatingFileHandler is configured; log file is created."""

    def test_log_file_created_after_setup(self, log_dir: Path) -> None:
        """AC-3: After setup_logging(), a log file exists in the log directory."""
        setup_logging(log_dir=log_dir, level="DEBUG")  # type: ignore[misc]
        logger = get_logger("rotation_test")  # type: ignore[misc]
        logger.info("Rotation test entry")
        log_files = list(log_dir.glob("*.log"))
        assert len(log_files) >= 1

    def test_logger_has_rotating_file_handler(self, log_dir: Path) -> None:
        """AC-3: The configured logger must include a RotatingFileHandler."""
        from logging.handlers import RotatingFileHandler

        setup_logging(log_dir=log_dir, level="DEBUG")  # type: ignore[misc]
        logger = get_logger("handler_check")  # type: ignore[misc]
        # Walk up the logger hierarchy to find handlers.
        current: logging.Logger | logging.RootLogger = logger
        handlers = list(current.handlers)
        while current.parent:  # type: ignore[union-attr]
            current = current.parent  # type: ignore[union-attr]
            handlers.extend(current.handlers)
        has_rotating = any(isinstance(h, RotatingFileHandler) for h in handlers)
        assert has_rotating, "No RotatingFileHandler found on the logger hierarchy"


# ---------------------------------------------------------------------------
# US-603 AC-4: Log directory auto-creation
# ---------------------------------------------------------------------------


class TestLoggerDirectoryAutoCreation:
    """AC-4: If the log directory does not exist, it is created automatically."""

    def test_nonexistent_log_dir_is_created(self, tmp_path: Path) -> None:
        """AC-4: setup_logging() creates the log directory if absent."""
        new_dir = tmp_path / "nested" / "log_dir"
        assert not new_dir.exists()
        setup_logging(log_dir=new_dir, level="DEBUG")  # type: ignore[misc]
        assert new_dir.exists()
