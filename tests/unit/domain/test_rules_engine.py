"""Unit tests for the rules engine (validation and move application)."""

from __future__ import annotations

import dataclasses

import pytest

from src.domain.board import Board
from src.domain.enums import GamePhase, MoveType, PlayerSide, PlayerType, Rank
from src.domain.game_state import GameState
from src.domain.move import Move
from src.domain.move_record import MoveRecord
from src.domain.piece import Piece
from src.domain.player import Player
from src.domain.position import Position
from src.domain.rules_engine import (
    RulesViolationError,
    ValidationResult,
    check_win_condition,
    validate_move,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RED = PlayerSide.RED
BLUE = PlayerSide.BLUE


def _piece(rank: Rank, side: PlayerSide, pos: Position, revealed: bool = False,
           has_moved: bool = False) -> Piece:
    """Construct a minimal Piece."""
    return Piece(rank=rank, owner=side, revealed=revealed, has_moved=has_moved, position=pos)


def _make_playing_state(
    red_pieces: list[Piece],
    blue_pieces: list[Piece],
    active: PlayerSide = RED,
    turn: int = 1,
    history: tuple[MoveRecord, ...] = (),
) -> GameState:
    """Build a minimal PLAYING GameState with the supplied pieces on the board."""
    board = Board.create_empty()
    for p in red_pieces + blue_pieces:
        board = board.place_piece(p, p.position)

    red_flag_pos = next((p.position for p in red_pieces if p.rank is Rank.FLAG), None)
    blue_flag_pos = next((p.position for p in blue_pieces if p.rank is Rank.FLAG), None)

    players: tuple[Player, Player] = (
        Player(side=RED, player_type=PlayerType.HUMAN,
               pieces_remaining=tuple(red_pieces), flag_position=red_flag_pos),
        Player(side=BLUE, player_type=PlayerType.HUMAN,
               pieces_remaining=tuple(blue_pieces), flag_position=blue_flag_pos),
    )
    return GameState(
        board=board,
        players=players,
        active_player=active,
        phase=GamePhase.PLAYING,
        turn_number=turn,
        move_history=history,
        winner=None,
    )


# ---------------------------------------------------------------------------
# Basic move validation
# ---------------------------------------------------------------------------


class TestValidNormalMove:
    """One-square orthogonal move is accepted."""

    def test_valid_single_step(self) -> None:
        """A Captain moving one square forward is legal."""
        pos = Position(7, 0)
        to = Position(6, 0)
        piece = _piece(Rank.CAPTAIN, RED, pos)
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))
        state = _make_playing_state([piece, red_flag], [blue_flag])
        move = Move(piece=piece, from_pos=pos, to_pos=to, move_type=MoveType.MOVE)
        assert validate_move(state, move) is ValidationResult.OK


class TestDiagonalMoveRejected:
    """Diagonal moves are always illegal."""

    def test_diagonal_rejected(self) -> None:
        """A piece cannot move diagonally."""
        pos = Position(7, 0)
        to = Position(6, 1)
        piece = _piece(Rank.CAPTAIN, RED, pos)
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))
        state = _make_playing_state([piece, red_flag], [blue_flag])
        move = Move(piece=piece, from_pos=pos, to_pos=to, move_type=MoveType.MOVE)
        assert validate_move(state, move) is ValidationResult.INVALID


class TestDistanceOneForNonScout:
    """Non-Scout pieces may not move more than one square."""

    def test_two_squares_rejected(self) -> None:
        """A Major cannot move two squares at once."""
        pos = Position(7, 0)
        to = Position(5, 0)
        piece = _piece(Rank.MAJOR, RED, pos)
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))
        state = _make_playing_state([piece, red_flag], [blue_flag])
        move = Move(piece=piece, from_pos=pos, to_pos=to, move_type=MoveType.MOVE)
        assert validate_move(state, move) is ValidationResult.INVALID


class TestMoveToLakeRejected:
    """No piece may move onto a lake square."""

    def test_lake_destination_rejected(self) -> None:
        """Moving to a lake square (4,2) is illegal."""
        pos = Position(3, 2)
        to = Position(4, 2)  # lake
        piece = _piece(Rank.CAPTAIN, RED, pos)
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))
        state = _make_playing_state([piece, red_flag], [blue_flag])
        move = Move(piece=piece, from_pos=pos, to_pos=to, move_type=MoveType.MOVE)
        assert validate_move(state, move) is ValidationResult.INVALID


class TestMoveToFriendlyRejected:
    """A piece cannot move onto a square occupied by a friendly piece."""

    def test_friendly_destination_rejected(self) -> None:
        """Moving onto a friendly piece is illegal."""
        pos = Position(7, 0)
        to = Position(6, 0)
        piece = _piece(Rank.CAPTAIN, RED, pos)
        blocker = _piece(Rank.SERGEANT, RED, to)
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))
        state = _make_playing_state([piece, blocker, red_flag], [blue_flag])
        move = Move(piece=piece, from_pos=pos, to_pos=to, move_type=MoveType.MOVE)
        assert validate_move(state, move) is ValidationResult.INVALID


class TestImmovablePieces:
    """BOMB and FLAG may never be moved."""

    def test_bomb_movement_rejected(self) -> None:
        """Bombs cannot be moved."""
        pos = Position(7, 0)
        to = Position(6, 0)
        piece = _piece(Rank.BOMB, RED, pos)
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))
        state = _make_playing_state([piece, red_flag], [blue_flag])
        move = Move(piece=piece, from_pos=pos, to_pos=to, move_type=MoveType.MOVE)
        assert validate_move(state, move) is ValidationResult.INVALID

    def test_flag_movement_rejected(self) -> None:
        """Flags cannot be moved."""
        pos = Position(9, 9)
        to = Position(8, 9)
        piece = _piece(Rank.FLAG, RED, pos)
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 0))
        state = _make_playing_state([piece], [blue_flag])
        move = Move(piece=piece, from_pos=pos, to_pos=to, move_type=MoveType.MOVE)
        assert validate_move(state, move) is ValidationResult.INVALID


class TestScoutMoves:
    """Scout special movement rules."""

    def test_scout_can_move_multiple_squares(self) -> None:
        """Scout moves multiple squares along an open column."""
        pos = Position(9, 0)
        to = Position(6, 0)
        piece = _piece(Rank.SCOUT, RED, pos)
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))
        state = _make_playing_state([piece, red_flag], [blue_flag])
        move = Move(piece=piece, from_pos=pos, to_pos=to, move_type=MoveType.MOVE)
        assert validate_move(state, move) is ValidationResult.OK

    def test_scout_blocked_by_friendly(self) -> None:
        """Scout cannot pass through a friendly piece."""
        pos = Position(9, 0)
        blocker_pos = Position(8, 0)
        to = Position(7, 0)
        piece = _piece(Rank.SCOUT, RED, pos)
        blocker = _piece(Rank.SERGEANT, RED, blocker_pos)
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))
        state = _make_playing_state([piece, blocker, red_flag], [blue_flag])
        move = Move(piece=piece, from_pos=pos, to_pos=to, move_type=MoveType.MOVE)
        assert validate_move(state, move) is ValidationResult.INVALID

    def test_scout_blocked_by_lake(self) -> None:
        """Scout cannot pass through a lake square."""
        # Moving from row 3 col 2 to row 6 col 2 would cross the lake at (4,2).
        pos = Position(3, 2)
        to = Position(6, 2)
        piece = _piece(Rank.SCOUT, RED, pos)
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))
        state = _make_playing_state([piece, red_flag], [blue_flag])
        move = Move(piece=piece, from_pos=pos, to_pos=to, move_type=MoveType.MOVE)
        assert validate_move(state, move) is ValidationResult.INVALID

    def test_scout_cannot_jump_over_enemy(self) -> None:
        """Scout cannot jump over an enemy piece."""
        pos = Position(9, 0)
        enemy_pos = Position(7, 0)
        to = Position(6, 0)
        piece = _piece(Rank.SCOUT, RED, pos)
        enemy = _piece(Rank.CAPTAIN, BLUE, enemy_pos)
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))
        state = _make_playing_state([piece, red_flag], [blue_flag, enemy])
        move = Move(piece=piece, from_pos=pos, to_pos=to, move_type=MoveType.MOVE)
        assert validate_move(state, move) is ValidationResult.INVALID


class TestTwoSquareRule:
    """Two-square oscillation rule."""

    def test_oscillation_rejected(self) -> None:
        """A piece that has already made two A→B, B→A trips is rejected on the third."""
        pos_a = Position(7, 0)
        pos_b = Position(6, 0)
        piece_a = _piece(Rank.CAPTAIN, RED, pos_a)
        piece_b = _piece(Rank.CAPTAIN, RED, pos_b, has_moved=True)
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))

        # Build artificial history showing two full round trips for this piece.
        def _record(from_p: Position, to_p: Position, piece: Piece, turn: int) -> MoveRecord:
            m = Move(piece=piece, from_pos=from_p, to_pos=to_p, move_type=MoveType.MOVE)
            return MoveRecord(move=m, combat_result=None, turn_number=turn, timestamp=0.0)

        history = (
            _record(pos_a, pos_b, piece_a, 1),  # first A→B
            _record(pos_b, pos_a, piece_b, 2),  # first B→A
        )

        state = _make_playing_state([piece_a, red_flag], [blue_flag], history=history)
        # Now trying A→B again should be rejected (third occurrence)
        move = Move(piece=piece_a, from_pos=pos_a, to_pos=pos_b, move_type=MoveType.MOVE)
        assert validate_move(state, move) is ValidationResult.INVALID


# ---------------------------------------------------------------------------
# Win condition tests
# ---------------------------------------------------------------------------


class TestFlagCaptureTriggerGameOver:
    """Capturing the flag ends the game."""

    def test_flag_captured_game_over(self) -> None:
        """When a player's flag is missing, the game transitions to GAME_OVER."""
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))
        state = _make_playing_state([red_flag], [blue_flag])
        # Simulate the blue flag being captured by creating board without blue flag
        board_no_flag = state.board.remove_piece(Position(0, 0))
        state_no_flag = dataclasses.replace(state, board=board_no_flag)
        result = check_win_condition(state_no_flag)
        assert result.phase is GamePhase.GAME_OVER
        assert result.winner is RED


class TestNoMovablePiecesLoses:
    """A player with only Bombs and Flag has no legal moves – opponent wins."""

    def test_only_bombs_and_flag_loses(self) -> None:
        """Active player with only immovable pieces → opponent wins."""
        red_bomb = _piece(Rank.BOMB, RED, Position(9, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))
        blue_captain = _piece(Rank.CAPTAIN, BLUE, Position(0, 0))
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 9))
        state = _make_playing_state(
            [red_bomb, red_flag], [blue_captain, blue_flag], active=RED
        )
        result = check_win_condition(state)
        assert result.phase is GamePhase.GAME_OVER
        assert result.winner is BLUE


class TestTurnLimitDraw:
    """Turn 3000 results in a draw."""

    def test_turn_3000_draw(self) -> None:
        """When turn_number >= 3000 the game is a draw with winner=None."""
        red_captain = _piece(Rank.CAPTAIN, RED, Position(9, 0))
        blue_captain = _piece(Rank.CAPTAIN, BLUE, Position(0, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 9))
        state = _make_playing_state(
            [red_captain, red_flag], [blue_captain, blue_flag], turn=3000
        )
        result = check_win_condition(state)
        assert result.phase is GamePhase.GAME_OVER
        assert result.winner is None


class TestRulesViolationError:
    """apply_move raises RulesViolationError on illegal moves."""

    def test_invalid_move_raises(self) -> None:
        """apply_move raises RulesViolationError for a diagonal move."""
        from src.domain.rules_engine import apply_move

        pos = Position(7, 0)
        to = Position(6, 1)
        piece = _piece(Rank.CAPTAIN, RED, pos)
        blue_flag = _piece(Rank.FLAG, BLUE, Position(0, 0))
        red_flag = _piece(Rank.FLAG, RED, Position(9, 9))
        state = _make_playing_state([piece, red_flag], [blue_flag])
        move = Move(piece=piece, from_pos=pos, to_pos=to, move_type=MoveType.ATTACK)
        with pytest.raises(RulesViolationError):
            apply_move(state, move)
