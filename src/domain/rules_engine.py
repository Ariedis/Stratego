"""
src/domain/rules_engine.py

Movement validation, placement validation, and win-condition detection.
Specification: game_components.md §4, §6, §7; data_models.md §4
"""
from __future__ import annotations

from enum import Enum

from src.domain.board import Board
from src.domain.enums import GamePhase, MoveType, PlayerSide, Rank
from src.domain.game_state import GameState, MoveRecord
from src.domain.move import Move
from src.domain.piece import Piece, Position
from src.domain.player import Player


class ValidationResult(Enum):
    """Result of a move-validation check."""

    OK = "OK"
    INVALID = "INVALID"


class RulesViolationError(Exception):
    """Raised for hard rules violations (e.g., attempting to move an immovable piece)."""


_IMMOVABLE_RANKS: frozenset[Rank] = frozenset({Rank.BOMB, Rank.FLAG})

# Maximum half-moves before declaring a draw (game_components.md §6).
MAX_TURNS: int = 3000


# ---------------------------------------------------------------------------
# Move validation
# ---------------------------------------------------------------------------


def validate_move(state: GameState, move: Move) -> ValidationResult:
    """Return ValidationResult.OK iff *move* is legal in *state*.

    Raises RulesViolationError for hard violations such as attempting to
    move an immovable piece.
    """
    piece = move.piece
    from_pos = move.from_pos
    to_pos = move.to_pos
    board = state.board

    # Hard violation: immovable pieces must never be moved.
    if piece.rank in _IMMOVABLE_RANKS:
        raise RulesViolationError(
            f"Piece {piece.rank.name} at {from_pos} is immovable and cannot be moved."
        )

    # Destination must be on the board.
    if not to_pos.is_valid():
        return ValidationResult.INVALID

    # Destination must not be a lake.
    if board.is_lake(to_pos):
        return ValidationResult.INVALID

    # Cannot move onto own piece.
    dest_sq = board.get_square(to_pos)
    if dest_sq.piece is not None and dest_sq.piece.owner == piece.owner:
        return ValidationResult.INVALID

    row_diff = to_pos.row - from_pos.row
    col_diff = to_pos.col - from_pos.col

    # Must be orthogonal (no diagonals).
    if row_diff != 0 and col_diff != 0:
        return ValidationResult.INVALID

    if piece.rank == Rank.SCOUT:
        return _validate_scout_move(board, from_pos, to_pos, piece)

    # Normal pieces move exactly one square.
    if abs(row_diff) + abs(col_diff) != 1:
        return ValidationResult.INVALID

    # Two-square rule check (game_components.md §4.4).
    if _violates_two_square_rule(state, move):
        return ValidationResult.INVALID

    return ValidationResult.OK


def _validate_scout_move(
    board: Board, from_pos: Position, to_pos: Position, piece: Piece
) -> ValidationResult:
    """Validate Scout long-range movement (game_components.md §4.2)."""
    row_diff = to_pos.row - from_pos.row
    col_diff = to_pos.col - from_pos.col

    # Must be orthogonal.
    if row_diff != 0 and col_diff != 0:
        return ValidationResult.INVALID

    # Cannot stay in place.
    if row_diff == 0 and col_diff == 0:
        return ValidationResult.INVALID

    # Determine step direction.
    row_step = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
    col_step = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)

    current = Position(from_pos.row + row_step, from_pos.col + col_step)
    while current != to_pos:
        if not current.is_valid():
            return ValidationResult.INVALID
        sq = board.get_square(current)
        # Lake blocks movement.
        if sq.terrain.name == "LAKE":
            return ValidationResult.INVALID
        # Any piece (friendly or enemy) blocks further movement.
        if sq.piece is not None:
            return ValidationResult.INVALID
        current = Position(current.row + row_step, current.col + col_step)

    # Check the destination square.
    dest_sq = board.get_square(to_pos)
    if dest_sq.terrain.name == "LAKE":
        return ValidationResult.INVALID
    if dest_sq.piece is not None and dest_sq.piece.owner == piece.owner:
        return ValidationResult.INVALID

    return ValidationResult.OK


def _violates_two_square_rule(state: GameState, move: Move) -> bool:
    """Return True iff *move* violates the two-square shuttling rule.

    Rule: a piece may not move back-and-forth between two squares more than
    two consecutive turns (game_components.md §4.4).
    """
    history = state.move_history
    if len(history) < 2:
        return False

    last = history[-1]
    second_last = history[-2]

    # Check if the last two moves by this piece were the same back-and-forth.
    piece_pos = (move.piece.position.row, move.piece.position.col)
    from_pos_t = (move.from_pos.row, move.from_pos.col)
    to_pos_t = (move.to_pos.row, move.to_pos.col)

    if (
        last.from_pos == from_pos_t
        and last.to_pos == to_pos_t
        and second_last.from_pos == to_pos_t
        and second_last.to_pos == from_pos_t
    ):
        return True
    return False


# ---------------------------------------------------------------------------
# Setup validation
# ---------------------------------------------------------------------------


def validate_placement(state: GameState, piece: Piece, pos: Position) -> ValidationResult:
    """Return OK iff *piece* can be placed at *pos* during the setup phase.

    Checks:
    - Position is within the active player's setup zone.
    - Position is not a lake.
    - Position is not already occupied.
    """
    board = state.board

    if board.is_lake(pos):
        return ValidationResult.INVALID

    sq = board.get_square(pos)
    if sq.piece is not None:
        return ValidationResult.INVALID

    if not board.is_in_setup_zone(pos, piece.owner):
        return ValidationResult.INVALID

    return ValidationResult.OK


def is_setup_complete(state: GameState) -> bool:
    """Return True iff both players have placed all 40 pieces."""
    for player in state.players:
        if len(player.pieces_remaining) != 40:
            return False
    return True


# ---------------------------------------------------------------------------
# Win condition detection
# ---------------------------------------------------------------------------


def check_win_condition(state: GameState) -> GameState:
    """Return a (possibly updated) GameState after applying win-condition checks.

    Transitions to GAME_OVER when:
    1. A player's Flag has been captured (detected via missing Flag piece).
    2. A player has no moveable pieces remaining.
    3. turn_number >= MAX_TURNS (draw — winner=None).
    """
    if state.phase != GamePhase.PLAYING:
        return state

    # Draw by turn limit.
    if state.turn_number >= MAX_TURNS:
        return _make_game_over(state, winner=None)

    # Find the inactive player (the one whose pieces could have been captured).
    for player in state.players:
        has_flag = any(p.rank == Rank.FLAG for p in player.pieces_remaining)
        if not has_flag:
            # This player's flag was captured → the other player wins.
            other_side = (
                PlayerSide.BLUE if player.side == PlayerSide.RED else PlayerSide.RED
            )
            return _make_game_over(state, winner=other_side)

    # No-moves-remaining check.
    inactive = _get_player(state, _other_side(state.active_player))
    if not _has_moveable_pieces(inactive.pieces_remaining):
        return _make_game_over(state, winner=state.active_player)

    return state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_game_over(state: GameState, winner: PlayerSide | None) -> GameState:
    from dataclasses import replace

    return replace(state, phase=GamePhase.GAME_OVER, winner=winner)


def _other_side(side: PlayerSide) -> PlayerSide:
    return PlayerSide.BLUE if side == PlayerSide.RED else PlayerSide.RED


def _get_player(state: GameState, side: PlayerSide) -> Player:
    for player in state.players:
        if player.side == side:
            return player
    raise ValueError(f"Player {side} not found in state.")


def _has_moveable_pieces(pieces: tuple[Piece, ...]) -> bool:
    """Return True iff at least one piece can move (not a BOMB or FLAG)."""
    return any(p.rank not in _IMMOVABLE_RANKS for p in pieces)
