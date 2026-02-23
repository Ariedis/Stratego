"""
test_full_game_session.py — Integration tests for complete game sessions.

Epic: EPIC-7 | User Story: US-706
Covers acceptance criteria:
  AC-1: Full scripted game session terminates with the expected winner.
  AC-3: AI-vs-AI game terminates within a reasonable bound.
Specification: All layers
"""
from __future__ import annotations

import pytest

from src.domain.board import Board
from src.domain.enums import GamePhase, PlayerSide, PlayerType, Rank
from src.domain.game_state import GameState
from src.domain.move import Move
from src.domain.piece import Piece, Position
from src.domain.player import Player
from src.domain.rules_engine import apply_move, check_win_condition

# ---------------------------------------------------------------------------
# Optional imports — application layer may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    import src.domain.rules_engine as _rules_engine_module
    from src.application.commands import MovePiece
    from src.application.event_bus import EventBus
    from src.application.game_controller import GameController

    _APP_LAYER_AVAILABLE = True
except ImportError:
    _APP_LAYER_AVAILABLE = False
    GameController = None  # type: ignore[assignment, misc]
    EventBus = None  # type: ignore[assignment, misc]
    MovePiece = None  # type: ignore[assignment, misc]
    _rules_engine_module = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_piece(
    rank: Rank,
    owner: PlayerSide,
    row: int,
    col: int,
    *,
    revealed: bool = False,
    has_moved: bool = False,
) -> Piece:
    return Piece(
        rank=rank,
        owner=owner,
        revealed=revealed,
        has_moved=has_moved,
        position=Position(row, col),
    )


def _make_player(
    side: PlayerSide,
    pieces: list[Piece],
    player_type: PlayerType = PlayerType.HUMAN,
) -> Player:
    flag_pos = next((p.position for p in pieces if p.rank == Rank.FLAG), None)
    return Player(
        side=side,
        player_type=player_type,
        pieces_remaining=tuple(pieces),
        flag_position=flag_pos,
    )


def _build_state(red_pieces: list[Piece], blue_pieces: list[Piece]) -> GameState:
    """Construct a minimal PLAYING GameState from piece lists."""
    board = Board.create_empty()
    for p in red_pieces + blue_pieces:
        board = board.place_piece(p)
    return GameState(
        board=board,
        players=(
            _make_player(PlayerSide.RED, red_pieces),
            _make_player(PlayerSide.BLUE, blue_pieces),
        ),
        active_player=PlayerSide.RED,
        phase=GamePhase.PLAYING,
        turn_number=1,
    )


# ---------------------------------------------------------------------------
# US-706 AC-1: Scripted two-piece game — Red captures Blue's Flag
# ---------------------------------------------------------------------------


class TestScriptedGameSession:
    """AC-1: A scripted session ends with the expected winner."""

    def test_red_wins_after_scout_draw_leaves_blue_immovable(self) -> None:
        """AC-1: After Scouts draw, Blue has only Flag (immovable) → Red wins."""
        # Red Scout at (8,0), Red Flag at (9,0)
        # Blue Flag at (0,0), Blue Scout at (1,0)
        red_scout = _make_piece(Rank.SCOUT, PlayerSide.RED, 8, 0)
        red_flag = _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0)
        blue_flag = _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0)
        blue_scout = _make_piece(Rank.SCOUT, PlayerSide.BLUE, 1, 0)

        state = _build_state([red_scout, red_flag], [blue_flag, blue_scout])

        # Red Scout long-moves to (2,0) — column 0 is clear between rows 8 and 2.
        move1 = Move(
            piece=red_scout,
            from_pos=Position(8, 0),
            to_pos=Position(2, 0),
        )
        state = apply_move(state, move1)
        assert state.phase == GamePhase.PLAYING

        # Red Scout (now at (2,0)) attacks Blue Scout at (1,0); equal ranks → draw.
        red_scout2 = state.board.get_square(Position(2, 0)).piece
        assert red_scout2 is not None

        move2 = Move(
            piece=red_scout2,
            from_pos=Position(2, 0),
            to_pos=Position(1, 0),
        )
        state = apply_move(state, move2)

        # Both Scouts are removed.  Blue now has only its Flag (immovable) →
        # win condition fires immediately: Red wins.
        assert state.phase == GamePhase.GAME_OVER
        assert state.winner == PlayerSide.RED

    def test_direct_flag_capture_ends_game(self) -> None:
        """AC-1: Any piece adjacent to the Flag can capture it in one move."""
        red_miner = _make_piece(Rank.MINER, PlayerSide.RED, 1, 0)
        red_flag = _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0)
        blue_flag = _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0)

        state = _build_state([red_miner, red_flag], [blue_flag])

        # Red Miner at (1,0) captures Blue Flag at (0,0).
        move = Move(
            piece=red_miner,
            from_pos=Position(1, 0),
            to_pos=Position(0, 0),
        )
        state = apply_move(state, move)
        assert state.phase == GamePhase.GAME_OVER
        assert state.winner == PlayerSide.RED

    def test_game_winner_is_none_mid_game(self) -> None:
        """AC-1 (negative): A normal mid-game state has no winner yet."""
        red_scout = _make_piece(Rank.SCOUT, PlayerSide.RED, 8, 0)
        red_flag = _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0)
        blue_flag = _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0)
        blue_scout = _make_piece(Rank.SCOUT, PlayerSide.BLUE, 1, 0)
        state = _build_state([red_scout, red_flag], [blue_flag, blue_scout])
        assert state.phase == GamePhase.PLAYING
        assert state.winner is None

    def test_no_moveable_pieces_triggers_game_over(self) -> None:
        """AC-1 (US-205 AC-2 integration): Blue with only Flag and Bomb → Red wins."""
        # Blue has only a Flag (immovable) and Bomb (immovable).
        red_scout = _make_piece(Rank.SCOUT, PlayerSide.RED, 8, 0)
        red_flag = _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0)
        blue_flag = _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0)
        blue_bomb = _make_piece(Rank.BOMB, PlayerSide.BLUE, 0, 1)

        state = _build_state([red_scout, red_flag], [blue_flag, blue_bomb])
        state = check_win_condition(state)
        assert state.phase == GamePhase.GAME_OVER
        assert state.winner == PlayerSide.RED


# ---------------------------------------------------------------------------
# US-706 AC-1: Multi-move scripted session via GameController
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    not _APP_LAYER_AVAILABLE,
    reason="Application layer (GameController/EventBus) not implemented yet",
    strict=False,
)
class TestGameControllerIntegration:
    """AC-1: Full scripted session via GameController ends with correct winner."""

    def test_game_controller_flag_capture_ends_game(self) -> None:
        """AC-1: GameController.submit_command() with Flag capture → GAME_OVER."""
        red_miner = _make_piece(Rank.MINER, PlayerSide.RED, 1, 0)
        red_flag = _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0)
        blue_flag = _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0)
        initial_state = _build_state([red_miner, red_flag], [blue_flag])

        event_bus = EventBus()  # type: ignore[misc]
        controller = GameController(initial_state, event_bus, _rules_engine_module)  # type: ignore[misc]

        cmd = MovePiece(from_pos=Position(1, 0), to_pos=Position(0, 0))  # type: ignore[misc]
        controller.submit_command(cmd)  # type: ignore[union-attr]

        assert controller.current_state.phase == GamePhase.GAME_OVER  # type: ignore[union-attr]
        assert controller.current_state.winner == PlayerSide.RED  # type: ignore[union-attr]

    def test_game_controller_turn_advances_after_valid_move(self) -> None:
        """AC-1: After a valid move the turn number increments."""
        red_scout = _make_piece(Rank.SCOUT, PlayerSide.RED, 8, 0)
        red_flag = _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0)
        blue_flag = _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0)
        blue_scout = _make_piece(Rank.SCOUT, PlayerSide.BLUE, 1, 0)
        initial_state = _build_state([red_scout, red_flag], [blue_flag, blue_scout])

        event_bus = EventBus()  # type: ignore[misc]
        controller = GameController(initial_state, event_bus, _rules_engine_module)  # type: ignore[misc]

        cmd = MovePiece(from_pos=Position(8, 0), to_pos=Position(7, 0))  # type: ignore[misc]
        controller.submit_command(cmd)  # type: ignore[union-attr]

        assert controller.current_state.turn_number > initial_state.turn_number  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-706 AC-3: Domain-layer AI-vs-AI terminates (simplified headless version)
# ---------------------------------------------------------------------------


class TestDomainLayerTermination:
    """AC-3 (simplified): A programmatic game session terminates within move limit."""

    def test_scripted_session_terminates(self) -> None:
        """AC-3: A short scripted sequence terminates correctly at GAME_OVER."""
        # Red Miner directly adjacent to Blue Flag — game ends in 1 move.
        red_miner = _make_piece(Rank.MINER, PlayerSide.RED, 1, 0)
        red_flag = _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0)
        blue_flag = _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0)

        state = _build_state([red_miner, red_flag], [blue_flag])
        move = Move(
            piece=red_miner,
            from_pos=Position(1, 0),
            to_pos=Position(0, 0),
        )
        state = apply_move(state, move)
        assert state.phase == GamePhase.GAME_OVER

    def test_draw_at_turn_limit(self) -> None:
        """AC-3 (US-205 AC-3): A game reaching 3000 half-moves is declared a draw."""
        from dataclasses import replace

        from src.domain.rules_engine import MAX_TURNS

        red_scout = _make_piece(Rank.SCOUT, PlayerSide.RED, 8, 0)
        red_flag = _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0)
        blue_flag = _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0)
        blue_scout = _make_piece(Rank.SCOUT, PlayerSide.BLUE, 1, 0)
        state = _build_state([red_scout, red_flag], [blue_flag, blue_scout])

        # Simulate that the game has reached MAX_TURNS.
        state = replace(state, turn_number=MAX_TURNS)
        move = Move(
            piece=red_scout,
            from_pos=Position(8, 0),
            to_pos=Position(7, 0),
        )
        state = apply_move(state, move)
        assert state.phase == GamePhase.GAME_OVER
        assert state.winner is None  # draw
