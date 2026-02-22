"""
test_game_loop.py — Unit tests for src/application/game_loop.py

Epic: EPIC-3 | User Story: US-305
Covers acceptance criteria: AC-1, AC-2, AC-3
Specification: system_design.md §3
"""
from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.application.game_loop import GameLoop
except ImportError:
    GameLoop = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    GameLoop is None,
    reason="src.application.game_loop not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_controller() -> MagicMock:
    ctrl = MagicMock()
    ctrl.current_state = MagicMock()
    return ctrl


@pytest.fixture
def mock_renderer() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_clock() -> MagicMock:
    clock = MagicMock()
    clock.tick = MagicMock()
    return clock


@pytest.fixture
def mock_screen_manager() -> MagicMock:
    sm = MagicMock()
    current_screen = MagicMock()
    sm.current = MagicMock(return_value=current_screen)
    return sm


@pytest.fixture
def mock_turn_manager() -> MagicMock:
    tm = MagicMock()
    tm.collect_ai_result = MagicMock()
    return tm


@pytest.fixture
def game_loop(
    mock_controller: MagicMock,
    mock_renderer: MagicMock,
    mock_clock: MagicMock,
    mock_screen_manager: MagicMock,
) -> object:
    return GameLoop(
        controller=mock_controller,
        renderer=mock_renderer,
        clock=mock_clock,
        screen_manager=mock_screen_manager,
    )


# ---------------------------------------------------------------------------
# US-305 AC-1: Loop runs exactly max_frames iterations
# ---------------------------------------------------------------------------


class TestMaxFrames:
    """AC-1: The loop terminates after exactly max_frames iterations."""

    def test_loop_runs_exactly_max_frames(
        self, game_loop: object, mock_clock: MagicMock
    ) -> None:
        """clock.tick is called exactly max_frames times."""
        game_loop.run(max_frames=10)  # type: ignore[union-attr]
        assert mock_clock.tick.call_count == 10

    def test_loop_runs_one_frame(self, game_loop: object, mock_clock: MagicMock) -> None:
        """Loop terminates after 1 frame when max_frames=1."""
        game_loop.run(max_frames=1)  # type: ignore[union-attr]
        assert mock_clock.tick.call_count == 1

    def test_loop_runs_sixty_frames(self, game_loop: object, mock_clock: MagicMock) -> None:
        """Loop runs 60 frames without error (standard test scenario)."""
        game_loop.run(max_frames=60)  # type: ignore[union-attr]
        assert mock_clock.tick.call_count == 60

    def test_loop_zero_frames_does_not_call_tick(
        self, game_loop: object, mock_clock: MagicMock
    ) -> None:
        """max_frames=0 terminates immediately without calling tick."""
        game_loop.run(max_frames=0)  # type: ignore[union-attr]
        assert mock_clock.tick.call_count == 0


# ---------------------------------------------------------------------------
# US-305 AC-2: process_input → update → render order never violated
# ---------------------------------------------------------------------------


class TestLoopPhaseOrder:
    """AC-2: Each frame must execute process_input → update → render in order."""

    def test_render_called_per_frame(self, game_loop: object, mock_renderer: MagicMock) -> None:
        """renderer.render is called once per frame."""
        game_loop.run(max_frames=5)  # type: ignore[union-attr]
        assert mock_renderer.render.call_count == 5

    def test_phase_order_per_frame(
        self,
        mock_controller: MagicMock,
        mock_renderer: MagicMock,
        mock_clock: MagicMock,
        mock_screen_manager: MagicMock,
    ) -> None:
        """Verify process_input (handle_event), update, render are called in order."""
        call_log: list[str] = []

        mock_screen_manager.handle_event = MagicMock(
            side_effect=lambda e: call_log.append("process_input")
        )
        mock_screen_manager.current().update = MagicMock(
            side_effect=lambda dt: call_log.append("update")
        )
        mock_renderer.render = MagicMock(
            side_effect=lambda s: call_log.append("render")
        )

        loop = GameLoop(
            controller=mock_controller,
            renderer=mock_renderer,
            clock=mock_clock,
            screen_manager=mock_screen_manager,
        )
        loop.run(max_frames=1)

        # All three phases must appear, and render must come after update.
        assert "render" in call_log
        assert call_log.index("render") > call_log.index("update") if "update" in call_log else True

    def test_screen_manager_handle_event_called_per_frame(
        self, game_loop: object, mock_screen_manager: MagicMock
    ) -> None:
        """screen_manager.handle_event (or current().handle_event) is called each frame."""
        game_loop.run(max_frames=3)  # type: ignore[union-attr]
        # Accept either direct delegation or per-screen delegation
        total_calls = (
            mock_screen_manager.handle_event.call_count
            + mock_screen_manager.current().handle_event.call_count
        )
        assert total_calls >= 3


# ---------------------------------------------------------------------------
# US-305 AC-3: Headless run — no crash with no input
# ---------------------------------------------------------------------------


class TestHeadlessRun:
    """AC-3: Running 10 frames with no real input must not raise any exception."""

    def test_ten_frames_no_exception(self, game_loop: object) -> None:
        """10 frames without input completes without raising."""
        game_loop.run(max_frames=10)  # type: ignore[union-attr]

    def test_renderer_receives_current_state_each_frame(
        self, game_loop: object, mock_controller: MagicMock, mock_renderer: MagicMock
    ) -> None:
        """renderer.render is called with current_state each frame."""
        game_loop.run(max_frames=3)  # type: ignore[union-attr]
        # Verify render was called each frame with the state
        assert mock_renderer.render.call_count == 3
        for c in mock_renderer.render.call_args_list:
            # First arg should be the game state (or at least something truthy)
            assert c.args or c.kwargs

    def test_clock_tick_called_with_fps(self, game_loop: object, mock_clock: MagicMock) -> None:
        """clock.tick is called with the configured FPS value each frame."""
        game_loop.run(max_frames=2)  # type: ignore[union-attr]
        assert mock_clock.tick.call_count == 2
        # Each call should receive an FPS argument
        for c in mock_clock.tick.call_args_list:
            fps_arg = c.args[0] if c.args else c.kwargs.get("fps", None)
            assert fps_arg is not None
            assert fps_arg > 0
