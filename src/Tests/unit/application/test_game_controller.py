"""
test_game_controller.py — Unit tests for src/application/game_controller.py

Epic: EPIC-3 | User Story: US-303
Covers acceptance criteria: AC-1, AC-2, AC-3, AC-4
Specification: system_design.md §4
"""
from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from src.domain.enums import GamePhase, PlayerSide, PlayerType, Rank
from src.domain.piece import Piece, Position
from src.Tests.fixtures.sample_game_states import (
    make_blue_piece,
    make_minimal_playing_state,
    make_red_piece,
)

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.application.commands import MovePiece, PlacePiece
    from src.application.event_bus import EventBus
    from src.application.events import (
        CombatResolved,
        GameOver,
        InvalidMove,
        PieceMoved,
        PiecePlaced,
    )
    from src.application.game_controller import GameController
except ImportError:
    GameController = None  # type: ignore[assignment, misc]
    MovePiece = None  # type: ignore[assignment, misc]
    PlacePiece = None  # type: ignore[assignment, misc]
    EventBus = None  # type: ignore[assignment, misc]
    PieceMoved = None  # type: ignore[assignment, misc]
    PiecePlaced = None  # type: ignore[assignment, misc]
    CombatResolved = None  # type: ignore[assignment, misc]
    GameOver = None  # type: ignore[assignment, misc]
    InvalidMove = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    GameController is None,
    reason="src.application.game_controller not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_event_bus() -> MagicMock:
    """A mock EventBus with a tracked publish() method."""
    bus = MagicMock()
    bus.subscribe = MagicMock()
    bus.publish = MagicMock()
    return bus


@pytest.fixture
def playing_state():  # type: ignore[return]
    """A minimal PLAYING state: Red Scout at (8,0), Red Flag at (9,0),
    Blue Scout at (1,0), Blue Flag at (0,0)."""
    return make_minimal_playing_state()


@pytest.fixture
def controller(playing_state, mock_event_bus):  # type: ignore[return]
    """A GameController wired to a mock event bus and real rules engine."""
    from src.domain import rules_engine

    return GameController(
        initial_state=playing_state,
        event_bus=mock_event_bus,
        rules_engine=rules_engine,
    )


# ---------------------------------------------------------------------------
# US-303 AC-1: Valid move — state updated and PieceMoved published
# ---------------------------------------------------------------------------


class TestValidMove:
    """AC-1: Valid move updates state and publishes PieceMoved."""

    def test_valid_move_updates_current_state(self, controller: object, mock_event_bus: MagicMock) -> None:
        """After a valid move the controller's current_state reflects the new turn."""
        initial_turn = controller.current_state.turn_number  # type: ignore[union-attr]
        cmd = MovePiece(from_pos=Position(8, 0), to_pos=Position(7, 0))
        controller.submit_command(cmd)  # type: ignore[union-attr]
        assert controller.current_state.turn_number == initial_turn + 1  # type: ignore[union-attr]

    def test_valid_move_publishes_piece_moved_event(self, controller: object, mock_event_bus: MagicMock) -> None:
        """After a valid move, PieceMoved is published exactly once."""
        cmd = MovePiece(from_pos=Position(8, 0), to_pos=Position(7, 0))
        controller.submit_command(cmd)  # type: ignore[union-attr]
        published_types = [type(c.args[0]) for c in mock_event_bus.publish.call_args_list]
        assert PieceMoved in published_types

    def test_valid_move_previous_state_unchanged(self, controller: object) -> None:
        """The state before submit_command is unaffected (immutability)."""
        old_state = controller.current_state  # type: ignore[union-attr]
        cmd = MovePiece(from_pos=Position(8, 0), to_pos=Position(7, 0))
        controller.submit_command(cmd)  # type: ignore[union-attr]
        # Old state should still reference turn 1
        assert old_state.turn_number == 1

    def test_current_state_property_is_readonly(self, controller: object) -> None:
        """current_state should be a read-only property (setting it raises AttributeError)."""
        with pytest.raises(AttributeError):
            controller.current_state = None  # type: ignore[union-attr, assignment]


# ---------------------------------------------------------------------------
# US-303 AC-2: Invalid move — state unchanged and InvalidMove published
# ---------------------------------------------------------------------------


class TestInvalidMove:
    """AC-2: Invalid move leaves state unchanged and publishes InvalidMove."""

    def test_invalid_move_to_lake_publishes_invalid_move_event(
        self, controller: object, mock_event_bus: MagicMock
    ) -> None:
        """Moving to a lake square triggers InvalidMove publication."""
        # Lake squares are at (4,2),(4,3),(5,2),(5,3),(4,6),(4,7),(5,6),(5,7)
        # Use a Scout that can reach row 4 col 2 in a single command — the
        # controller should reject it via rules engine.
        cmd = MovePiece(from_pos=Position(8, 0), to_pos=Position(4, 2))
        controller.submit_command(cmd)  # type: ignore[union-attr]
        published_types = [type(c.args[0]) for c in mock_event_bus.publish.call_args_list]
        assert InvalidMove in published_types

    def test_invalid_move_does_not_update_state(self, controller: object) -> None:
        """State turn number is unchanged after an invalid move."""
        initial_turn = controller.current_state.turn_number  # type: ignore[union-attr]
        # Moving to a lake is always invalid
        cmd = MovePiece(from_pos=Position(8, 0), to_pos=Position(4, 2))
        controller.submit_command(cmd)  # type: ignore[union-attr]
        assert controller.current_state.turn_number == initial_turn

    def test_invalid_move_to_own_piece_publishes_invalid_move(
        self, controller: object, mock_event_bus: MagicMock
    ) -> None:
        """Moving onto a friendly piece publishes InvalidMove."""
        # Flag is at (9,0); Scout at (8,0) — moving Scout to (9,0) is invalid.
        cmd = MovePiece(from_pos=Position(8, 0), to_pos=Position(9, 0))
        controller.submit_command(cmd)  # type: ignore[union-attr]
        published_types = [type(c.args[0]) for c in mock_event_bus.publish.call_args_list]
        assert InvalidMove in published_types


# ---------------------------------------------------------------------------
# US-303 AC-3: Combat move — CombatResolved published
# ---------------------------------------------------------------------------


class TestCombatMove:
    """AC-3: A move that results in combat publishes CombatResolved."""

    def test_combat_move_publishes_combat_resolved_event(self, mock_event_bus: MagicMock) -> None:
        """Attacking an enemy piece triggers CombatResolved publication."""
        # Red General at (8,0), Blue Colonel at (7,0) — Red attacks Blue.
        red_general = make_red_piece(Rank.GENERAL, 8, 0)
        blue_colonel = make_blue_piece(Rank.COLONEL, 7, 0)
        state = make_minimal_playing_state(
            red_pieces=[red_general, make_red_piece(Rank.FLAG, 9, 0)],
            blue_pieces=[blue_colonel, make_blue_piece(Rank.FLAG, 0, 0)],
        )
        from src.domain import rules_engine

        ctrl = GameController(
            initial_state=state,
            event_bus=mock_event_bus,
            rules_engine=rules_engine,
        )
        cmd = MovePiece(from_pos=Position(8, 0), to_pos=Position(7, 0))
        ctrl.submit_command(cmd)
        published_types = [type(c.args[0]) for c in mock_event_bus.publish.call_args_list]
        assert CombatResolved in published_types

    def test_combat_resolved_event_has_correct_winner(self, mock_event_bus: MagicMock) -> None:
        """CombatResolved event carries the correct winner (PlayerSide)."""
        red_marshal = make_red_piece(Rank.MARSHAL, 8, 0)
        blue_scout = make_blue_piece(Rank.SCOUT, 7, 0)
        state = make_minimal_playing_state(
            red_pieces=[red_marshal, make_red_piece(Rank.FLAG, 9, 0)],
            blue_pieces=[blue_scout, make_blue_piece(Rank.FLAG, 0, 0)],
        )
        from src.domain import rules_engine

        ctrl = GameController(
            initial_state=state,
            event_bus=mock_event_bus,
            rules_engine=rules_engine,
        )
        ctrl.submit_command(MovePiece(from_pos=Position(8, 0), to_pos=Position(7, 0)))
        combat_event = next(
            c.args[0]
            for c in mock_event_bus.publish.call_args_list
            if isinstance(c.args[0], CombatResolved)
        )
        assert combat_event.winner == PlayerSide.RED


# ---------------------------------------------------------------------------
# US-303 AC-4: Flag capture — GameOver published
# ---------------------------------------------------------------------------


class TestFlagCapture:
    """AC-4: Capturing the opponent's Flag publishes GameOver with the correct winner."""

    def test_flag_capture_publishes_game_over_event(self, mock_event_bus: MagicMock) -> None:
        """Capturing the Blue Flag causes a GameOver event to be published."""
        red_scout = make_red_piece(Rank.SCOUT, 1, 0)
        blue_flag = make_blue_piece(Rank.FLAG, 0, 0)
        state = make_minimal_playing_state(
            red_pieces=[red_scout, make_red_piece(Rank.FLAG, 9, 0)],
            blue_pieces=[blue_flag],
        )
        from src.domain import rules_engine

        ctrl = GameController(
            initial_state=state,
            event_bus=mock_event_bus,
            rules_engine=rules_engine,
        )
        ctrl.submit_command(MovePiece(from_pos=Position(1, 0), to_pos=Position(0, 0)))
        published_types = [type(c.args[0]) for c in mock_event_bus.publish.call_args_list]
        assert GameOver in published_types

    def test_flag_capture_game_over_winner_is_red(self, mock_event_bus: MagicMock) -> None:
        """GameOver event carries RED as the winner when Red captures the Flag."""
        red_scout = make_red_piece(Rank.SCOUT, 1, 0)
        blue_flag = make_blue_piece(Rank.FLAG, 0, 0)
        state = make_minimal_playing_state(
            red_pieces=[red_scout, make_red_piece(Rank.FLAG, 9, 0)],
            blue_pieces=[blue_flag],
        )
        from src.domain import rules_engine

        ctrl = GameController(
            initial_state=state,
            event_bus=mock_event_bus,
            rules_engine=rules_engine,
        )
        ctrl.submit_command(MovePiece(from_pos=Position(1, 0), to_pos=Position(0, 0)))
        game_over_event = next(
            c.args[0]
            for c in mock_event_bus.publish.call_args_list
            if isinstance(c.args[0], GameOver)
        )
        assert game_over_event.winner == PlayerSide.RED

    def test_game_state_phase_is_game_over_after_flag_capture(self, mock_event_bus: MagicMock) -> None:
        """After flag capture, current_state.phase is GAME_OVER."""
        red_scout = make_red_piece(Rank.SCOUT, 1, 0)
        blue_flag = make_blue_piece(Rank.FLAG, 0, 0)
        state = make_minimal_playing_state(
            red_pieces=[red_scout, make_red_piece(Rank.FLAG, 9, 0)],
            blue_pieces=[blue_flag],
        )
        from src.domain import rules_engine

        ctrl = GameController(
            initial_state=state,
            event_bus=mock_event_bus,
            rules_engine=rules_engine,
        )
        ctrl.submit_command(MovePiece(from_pos=Position(1, 0), to_pos=Position(0, 0)))
        assert ctrl.current_state.phase == GamePhase.GAME_OVER


# ---------------------------------------------------------------------------
# US-303: PlacePiece command routing
# ---------------------------------------------------------------------------


class TestPlacePieceCommand:
    """PlacePiece command routes correctly through the controller."""

    def test_valid_placement_publishes_piece_placed_event(self, mock_event_bus: MagicMock) -> None:
        """A valid PlacePiece command publishes PiecePlaced."""
        from src.domain.enums import GamePhase
        from src.domain.board import Board
        from src.domain.game_state import GameState
        from src.domain.player import Player
        from src.domain import rules_engine

        board = Board.create_empty()
        red_player = Player(
            side=PlayerSide.RED, player_type=PlayerType.HUMAN, pieces_remaining=()
        )
        blue_player = Player(
            side=PlayerSide.BLUE, player_type=PlayerType.HUMAN, pieces_remaining=()
        )
        setup_state = GameState(
            board=board,
            players=(red_player, blue_player),
            active_player=PlayerSide.RED,
            phase=GamePhase.SETUP,
            turn_number=0,
        )
        ctrl = GameController(
            initial_state=setup_state,
            event_bus=mock_event_bus,
            rules_engine=rules_engine,
        )
        scout = Piece(
            rank=Rank.SCOUT,
            owner=PlayerSide.RED,
            revealed=False,
            has_moved=False,
            position=Position(8, 0),
        )
        ctrl.submit_command(PlacePiece(piece=scout, pos=Position(8, 0)))
        published_types = [type(c.args[0]) for c in mock_event_bus.publish.call_args_list]
        assert PiecePlaced in published_types
