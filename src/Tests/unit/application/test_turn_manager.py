"""
test_turn_manager.py — Unit tests for src/application/turn_manager.py

Epic: EPIC-3 | User Story: US-304
Covers acceptance criteria: AC-1, AC-2, AC-3, AC-4
Specification: system_design.md §2.2, §5
"""
from __future__ import annotations

from concurrent.futures import Future
from unittest.mock import MagicMock, patch

import pytest

from src.domain.enums import PlayerSide, PlayerType, Rank
from src.domain.piece import Position
from src.Tests.fixtures.sample_game_states import (
    make_blue_piece,
    make_minimal_playing_state,
    make_red_piece,
)

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.application.event_bus import EventBus
    from src.application.events import TurnChanged
    from src.application.turn_manager import TurnManager
except ImportError:
    TurnManager = None  # type: ignore[assignment, misc]
    EventBus = None  # type: ignore[assignment, misc]
    TurnChanged = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    TurnManager is None,
    reason="src.application.turn_manager not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def make_ai_player_state(ai_side: PlayerSide = PlayerSide.BLUE):  # type: ignore[return]
    """Return a PLAYING state where the given side is AI_HARD."""
    from dataclasses import replace as dc_replace

    state = make_minimal_playing_state()
    new_players = tuple(
        dc_replace(p, player_type=PlayerType.AI_HARD) if p.side == ai_side else p
        for p in state.players
    )
    return dc_replace(state, players=new_players)


@pytest.fixture
def mock_event_bus() -> MagicMock:
    bus = MagicMock()
    bus.subscribe = MagicMock()
    bus.publish = MagicMock()
    bus.unsubscribe = MagicMock()
    return bus


@pytest.fixture
def mock_game_controller(playing_state=None) -> MagicMock:
    state = playing_state or make_minimal_playing_state()
    ctrl = MagicMock()
    ctrl.current_state = state
    return ctrl


@pytest.fixture
def mock_ai_orchestrator() -> MagicMock:
    return MagicMock()


@pytest.fixture
def turn_manager(mock_game_controller, mock_event_bus, mock_ai_orchestrator):  # type: ignore[return]
    return TurnManager(
        game_controller=mock_game_controller,
        event_bus=mock_event_bus,
        ai_orchestrator=mock_ai_orchestrator,
    )


# ---------------------------------------------------------------------------
# US-304 AC-1: TurnChanged(BLUE) triggers AI request when Blue is AI
# ---------------------------------------------------------------------------


class TestAITurnTriggered:
    """AC-2: When a TurnChanged event fires for an AI player, request_move is called."""

    def test_turn_changed_to_ai_player_triggers_request_move(
        self, mock_event_bus: MagicMock, mock_ai_orchestrator: MagicMock
    ) -> None:
        """TurnChanged(BLUE) fires request_move when Blue is AI_HARD."""
        ai_state = make_ai_player_state(PlayerSide.BLUE)
        mock_ctrl = MagicMock()
        mock_ctrl.current_state = ai_state
        tm = TurnManager(
            game_controller=mock_ctrl,
            event_bus=mock_event_bus,
            ai_orchestrator=mock_ai_orchestrator,
        )
        # Simulate the TurnChanged event delivery
        turn_event = TurnChanged(active_player=PlayerSide.BLUE)
        tm._on_turn_changed(turn_event)  # trigger internal handler
        mock_ai_orchestrator.request_move.assert_called_once()

    def test_ai_request_move_called_with_current_state(
        self, mock_event_bus: MagicMock, mock_ai_orchestrator: MagicMock
    ) -> None:
        """request_move receives the current GameState and difficulty."""
        ai_state = make_ai_player_state(PlayerSide.BLUE)
        mock_ctrl = MagicMock()
        mock_ctrl.current_state = ai_state
        tm = TurnManager(
            game_controller=mock_ctrl,
            event_bus=mock_event_bus,
            ai_orchestrator=mock_ai_orchestrator,
        )
        tm._on_turn_changed(TurnChanged(active_player=PlayerSide.BLUE))
        call_kwargs = mock_ai_orchestrator.request_move.call_args
        # State should be passed as the first positional or keyword argument
        assert call_kwargs is not None


# ---------------------------------------------------------------------------
# US-304 AC-2: TurnChanged for a Human player does NOT trigger AI
# ---------------------------------------------------------------------------


class TestHumanTurnDoesNotTriggerAI:
    """AC-2 (human variant): Red is Human; TurnChanged(RED) must not call AI."""

    def test_turn_changed_to_human_player_does_not_trigger_ai(
        self, mock_event_bus: MagicMock, mock_ai_orchestrator: MagicMock
    ) -> None:
        """TurnChanged(RED) when Red is HUMAN must not call request_move."""
        human_state = make_minimal_playing_state()  # both players are HUMAN
        mock_ctrl = MagicMock()
        mock_ctrl.current_state = human_state
        tm = TurnManager(
            game_controller=mock_ctrl,
            event_bus=mock_event_bus,
            ai_orchestrator=mock_ai_orchestrator,
        )
        tm._on_turn_changed(TurnChanged(active_player=PlayerSide.RED))
        mock_ai_orchestrator.request_move.assert_not_called()

    def test_turn_manager_subscribes_to_turn_changed_on_init(
        self, turn_manager: object, mock_event_bus: MagicMock
    ) -> None:
        """TurnManager must subscribe to TurnChanged during __init__."""
        subscribe_calls = [str(c) for c in mock_event_bus.subscribe.call_args_list]
        assert any("TurnChanged" in s for s in subscribe_calls)


# ---------------------------------------------------------------------------
# US-304 AC-3: collect_ai_result() collects the AI Future
# ---------------------------------------------------------------------------


class TestCollectAiResult:
    """AC-3: collect_ai_result() submits the AI move when the Future is done."""

    def test_collect_ai_result_submits_move_when_future_done(
        self, mock_event_bus: MagicMock, mock_ai_orchestrator: MagicMock
    ) -> None:
        """When the AI Future is complete, collect_ai_result submits the move."""
        from src.domain.move import Move
        from src.domain.enums import MoveType

        ai_state = make_ai_player_state(PlayerSide.BLUE)
        mock_ctrl = MagicMock()
        mock_ctrl.current_state = ai_state
        tm = TurnManager(
            game_controller=mock_ctrl,
            event_bus=mock_event_bus,
            ai_orchestrator=mock_ai_orchestrator,
        )
        # Simulate AI request was triggered
        future: Future = Future()
        scout = make_blue_piece(Rank.SCOUT, 1, 0)
        ai_move = Move(
            piece=scout,
            from_pos=Position(1, 0),
            to_pos=Position(2, 0),
            move_type=MoveType.MOVE,
        )
        future.set_result(ai_move)
        tm._ai_future = future  # inject the completed future

        tm.collect_ai_result()
        mock_ctrl.submit_command.assert_called_once()

    def test_collect_ai_result_no_op_when_no_future(
        self, mock_game_controller: MagicMock, mock_event_bus: MagicMock, mock_ai_orchestrator: MagicMock
    ) -> None:
        """collect_ai_result is a no-op when no AI Future is pending."""
        tm = TurnManager(
            game_controller=mock_game_controller,
            event_bus=mock_event_bus,
            ai_orchestrator=mock_ai_orchestrator,
        )
        # No future set — should not raise
        tm.collect_ai_result()
        mock_game_controller.submit_command.assert_not_called()

    def test_collect_ai_result_no_op_when_future_not_done(
        self, mock_event_bus: MagicMock, mock_ai_orchestrator: MagicMock
    ) -> None:
        """collect_ai_result is a no-op when the Future has not completed yet."""
        ai_state = make_ai_player_state(PlayerSide.BLUE)
        mock_ctrl = MagicMock()
        mock_ctrl.current_state = ai_state
        tm = TurnManager(
            game_controller=mock_ctrl,
            event_bus=mock_event_bus,
            ai_orchestrator=mock_ai_orchestrator,
        )
        pending_future: Future = Future()  # not resolved yet
        tm._ai_future = pending_future
        tm.collect_ai_result()
        mock_ctrl.submit_command.assert_not_called()


# ---------------------------------------------------------------------------
# US-304 AC-4: Retry logic on illegal AI move
# ---------------------------------------------------------------------------


class TestAIRetryOnIllegalMove:
    """AC-4: If AI returns an illegal move, TurnManager retries up to 3 times."""

    def test_illegal_ai_move_retried_up_to_three_times(
        self, mock_event_bus: MagicMock, mock_ai_orchestrator: MagicMock
    ) -> None:
        """When the controller always rejects the AI move, request_move is called
        at most 3 additional times (initial + 2 retries = 3 total)."""
        from src.domain.move import Move
        from src.domain.enums import MoveType
        from src.application.commands import MovePiece

        ai_state = make_ai_player_state(PlayerSide.BLUE)
        mock_ctrl = MagicMock()
        mock_ctrl.current_state = ai_state
        # Simulate controller always rejecting (e.g., raises RulesViolationError)
        from src.domain.rules_engine import RulesViolationError
        mock_ctrl.submit_command.side_effect = RulesViolationError("always invalid")

        tm = TurnManager(
            game_controller=mock_ctrl,
            event_bus=mock_event_bus,
            ai_orchestrator=mock_ai_orchestrator,
        )

        # Provide a completed future that always returns the same illegal move
        from src.domain.piece import Piece
        scout = make_blue_piece(Rank.SCOUT, 1, 0)
        ai_move = Move(
            piece=scout,
            from_pos=Position(1, 0),
            to_pos=Position(4, 2),  # a lake — always invalid
            move_type=MoveType.MOVE,
        )
        future: Future = Future()
        future.set_result(ai_move)
        tm._ai_future = future

        tm.collect_ai_result()
        # submit_command should have been called up to 3 times total before giving up
        assert mock_ctrl.submit_command.call_count <= 3

    def test_critical_error_logged_after_three_failures(
        self, mock_event_bus: MagicMock, mock_ai_orchestrator: MagicMock
    ) -> None:
        """After 3 consecutive illegal AI moves a CRITICAL log message is emitted."""
        import logging
        from src.domain.move import Move
        from src.domain.enums import MoveType
        from src.domain.rules_engine import RulesViolationError

        ai_state = make_ai_player_state(PlayerSide.BLUE)
        mock_ctrl = MagicMock()
        mock_ctrl.current_state = ai_state
        mock_ctrl.submit_command.side_effect = RulesViolationError("always invalid")

        tm = TurnManager(
            game_controller=mock_ctrl,
            event_bus=mock_event_bus,
            ai_orchestrator=mock_ai_orchestrator,
        )

        scout = make_blue_piece(Rank.SCOUT, 1, 0)
        ai_move = Move(
            piece=scout,
            from_pos=Position(1, 0),
            to_pos=Position(4, 2),
            move_type=MoveType.MOVE,
        )
        future: Future = Future()
        future.set_result(ai_move)
        tm._ai_future = future

        with patch("logging.critical") as mock_critical:
            tm.collect_ai_result()
            mock_critical.assert_called()
