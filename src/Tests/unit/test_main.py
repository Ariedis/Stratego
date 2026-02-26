"""
test_main.py — Unit tests for src/__main__.py

Epic: EPIC-3 | User Story: US-305
Covers: Application entry point, argument parsing, initialization, and main loop launch
Specification: system_design.md §1
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.__main__ import _build_initial_state, _parse_args, main
except ImportError:
    _build_initial_state = None  # type: ignore[assignment, misc]
    _parse_args = None  # type: ignore[assignment, misc]
    main = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    _parse_args is None,
    reason="src.__main__ not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# TestParseArgs: CLI argument parsing
# ---------------------------------------------------------------------------


class TestParseArgs:
    """Tests for _parse_args() function — validates CLI argument parsing."""

    def test_default_config_path(self) -> None:
        """Default --config is Path('~/.stratego/config.yaml')."""
        args = _parse_args([])  # type: ignore[misc]
        assert args.config == Path("~/.stratego/config.yaml")

    def test_default_log_level(self) -> None:
        """Default --log-level is 'INFO'."""
        args = _parse_args([])  # type: ignore[misc]
        assert args.log_level == "INFO"

    def test_custom_config_path(self) -> None:
        """--config accepts a custom path."""
        custom_path = "/tmp/my_config.yaml"
        args = _parse_args(["--config", custom_path])  # type: ignore[misc]
        assert args.config == Path(custom_path)

    def test_custom_log_level_debug(self) -> None:
        """--log-level DEBUG is accepted."""
        args = _parse_args(["--log-level", "DEBUG"])  # type: ignore[misc]
        assert args.log_level == "DEBUG"

    def test_custom_log_level_warning(self) -> None:
        """--log-level WARNING is accepted."""
        args = _parse_args(["--log-level", "WARNING"])  # type: ignore[misc]
        assert args.log_level == "WARNING"

    def test_custom_log_level_error(self) -> None:
        """--log-level ERROR is accepted."""
        args = _parse_args(["--log-level", "ERROR"])  # type: ignore[misc]
        assert args.log_level == "ERROR"

    def test_custom_log_level_critical(self) -> None:
        """--log-level CRITICAL is accepted."""
        args = _parse_args(["--log-level", "CRITICAL"])  # type: ignore[misc]
        assert args.log_level == "CRITICAL"

    def test_invalid_log_level_causes_system_exit(self) -> None:
        """Invalid --log-level causes SystemExit."""
        with pytest.raises(SystemExit):
            _parse_args(["--log-level", "INVALID"])  # type: ignore[misc]


# ---------------------------------------------------------------------------
# TestBuildInitialState: Domain state initialization
# ---------------------------------------------------------------------------


class TestBuildInitialState:
    """Tests for _build_initial_state() — validates initial GameState creation."""

    def test_returns_game_state_in_setup_phase(self) -> None:
        """Returns a GameState in SETUP phase."""
        try:
            from src.domain.enums import GamePhase
        except ImportError:
            pytest.skip("src.domain.enums not available")

        state = _build_initial_state()  # type: ignore[misc]
        assert state.phase == GamePhase.SETUP

    def test_active_player_is_red(self) -> None:
        """Active player is RED at game start."""
        try:
            from src.domain.enums import PlayerSide
        except ImportError:
            pytest.skip("src.domain.enums not available")

        state = _build_initial_state()  # type: ignore[misc]
        assert state.active_player == PlayerSide.RED

    def test_both_players_are_human(self) -> None:
        """Both players start as HUMAN type."""
        try:
            from src.domain.enums import PlayerType
        except ImportError:
            pytest.skip("src.domain.enums not available")

        state = _build_initial_state()  # type: ignore[misc]
        assert len(state.players) == 2
        assert state.players[0].player_type == PlayerType.HUMAN
        assert state.players[1].player_type == PlayerType.HUMAN

    def test_board_is_empty(self) -> None:
        """Board has no pieces placed initially."""
        state = _build_initial_state()  # type: ignore[misc]
        # Count all pieces on the board
        try:
            from src.domain.board import Position
        except ImportError:
            pytest.skip("src.domain.board not available")

        piece_count = 0
        for row in range(10):
            for col in range(10):
                pos = Position(row, col)
                square = state.board.get_square(pos)
                if square.piece is not None:
                    piece_count += 1
        assert piece_count == 0

    def test_turn_number_is_zero(self) -> None:
        """Turn number starts at 0."""
        state = _build_initial_state()  # type: ignore[misc]
        assert state.turn_number == 0


# ---------------------------------------------------------------------------
# TestMain: Application entry point and error handling
# ---------------------------------------------------------------------------


class TestMain:
    """Tests for main() — validates application bootstrap and error handling."""

    def test_main_with_import_error_calls_sys_exit(self) -> None:
        """When _launch_pygame raises ImportError, sys.exit(1) is called."""
        with patch("src.__main__._launch_pygame") as mock_launch:
            mock_launch.side_effect = ImportError("pygame not installed")

            with pytest.raises(SystemExit) as exc_info:
                main([])  # type: ignore[misc]

            assert exc_info.value.code == 1

    def test_main_with_generic_exception_calls_sys_exit(self) -> None:
        """When _launch_pygame raises a generic Exception, sys.exit(1) is called."""
        with patch("src.__main__._launch_pygame") as mock_launch:
            mock_launch.side_effect = RuntimeError("Display initialization failed")

            with pytest.raises(SystemExit) as exc_info:
                main([])  # type: ignore[misc]

            assert exc_info.value.code == 1

    def test_main_success_does_not_call_sys_exit(self) -> None:
        """When _launch_pygame succeeds, no sys.exit is called."""
        with (
            patch("src.__main__._launch_pygame") as mock_launch,
            patch("src.__main__.setup_logging"),
            patch("src.__main__.Config.load") as mock_config_load,
        ):
            mock_launch.return_value = None
            mock_config = MagicMock()
            mock_config.display.resolution = (800, 600)
            mock_config.display.fps_cap = 60
            mock_config.display.fullscreen = False
            mock_config_load.return_value = mock_config

            # Should not raise SystemExit
            main([])  # type: ignore[misc]

            # Verify _launch_pygame was called
            assert mock_launch.call_count == 1

    def test_main_uses_default_config_path(self) -> None:
        """main([]) uses default config path ~/.stratego/config.yaml."""
        with (
            patch("src.__main__._launch_pygame"),
            patch("src.__main__.setup_logging"),
            patch("src.__main__.Config.load") as mock_config_load,
        ):
            mock_config = MagicMock()
            mock_config.display.resolution = (800, 600)
            mock_config.display.fps_cap = 60
            mock_config.display.fullscreen = False
            mock_config_load.return_value = mock_config

            main([])  # type: ignore[misc]

            # Verify Config.load was called
            assert mock_config_load.call_count == 1
            # First positional arg should be the expanded default path
            actual_path = mock_config_load.call_args[0][0]
            assert "stratego" in str(actual_path).lower()
            assert "config.yaml" in str(actual_path).lower()

    def test_main_with_custom_config_path(self) -> None:
        """main(['--config', '/tmp/custom.yaml']) uses the custom path."""
        with (
            patch("src.__main__._launch_pygame"),
            patch("src.__main__.setup_logging"),
            patch("src.__main__.Config.load") as mock_config_load,
        ):
            mock_config = MagicMock()
            mock_config.display.resolution = (800, 600)
            mock_config.display.fps_cap = 60
            mock_config.display.fullscreen = False
            mock_config_load.return_value = mock_config

            main(["--config", "/tmp/custom.yaml"])  # type: ignore[misc]

            # Verify Config.load was called with custom path
            assert mock_config_load.call_count == 1
            actual_path = mock_config_load.call_args[0][0]
            assert actual_path.as_posix() == "/tmp/custom.yaml"

    def test_main_sets_up_logging(self) -> None:
        """main() calls setup_logging with correct parameters."""
        with (
            patch("src.__main__._launch_pygame"),
            patch("src.__main__.setup_logging") as mock_setup_logging,
            patch("src.__main__.Config.load") as mock_config_load,
        ):
            mock_config = MagicMock()
            mock_config.display.resolution = (800, 600)
            mock_config.display.fps_cap = 60
            mock_config.display.fullscreen = False
            mock_config_load.return_value = mock_config

            main(["--log-level", "DEBUG"])  # type: ignore[misc]

            # Verify setup_logging was called
            assert mock_setup_logging.call_count == 1
            call_args = mock_setup_logging.call_args
            # Check that level was set to DEBUG
            assert call_args.kwargs.get("level") == "DEBUG"
            assert call_args.kwargs.get("console") is True

    def test_main_builds_initial_state(self) -> None:
        """main() calls _build_initial_state and passes it to _launch_pygame."""
        with (
            patch("src.__main__._launch_pygame") as mock_launch,
            patch("src.__main__.setup_logging"),
            patch("src.__main__.Config.load") as mock_config_load,
            patch("src.__main__._build_initial_state") as mock_build_state,
        ):
            mock_config = MagicMock()
            mock_config.display.resolution = (800, 600)
            mock_config.display.fps_cap = 60
            mock_config.display.fullscreen = False
            mock_config_load.return_value = mock_config

            mock_state = MagicMock()
            mock_build_state.return_value = mock_state

            main([])  # type: ignore[misc]

            # Verify _build_initial_state was called
            assert mock_build_state.call_count == 1

            # Verify _launch_pygame received the state
            assert mock_launch.call_count == 1
            assert mock_launch.call_args[0][1] == mock_state
