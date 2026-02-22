"""Rules engine – validates and applies all legal Stratego game actions."""

from __future__ import annotations

import dataclasses
from enum import Enum

from src.domain.board import Board
from src.domain.combat import resolve_combat
from src.domain.enums import GamePhase, MoveType, PlayerSide, Rank, TerrainType
from src.domain.game_state import GameState
from src.domain.move import Move
from src.domain.move_record import MoveRecord
from src.domain.piece import Piece
from src.domain.player import Player
from src.domain.position import Position

# Maximum turns before the game is declared a draw.
_MAX_TURNS: int = 3000

# Number of pieces per side in a standard Stratego game.
_PIECES_PER_SIDE: int = 40


class RulesViolationError(Exception):
    """Raised when a requested action violates the rules of Stratego."""


class ValidationResult(Enum):
    """Result of a rules validation check."""

    OK = "OK"
    INVALID = "INVALID"


# ---------------------------------------------------------------------------
# Placement (setup phase)
# ---------------------------------------------------------------------------


def validate_placement(state: GameState, cmd: PlacementCommand) -> ValidationResult:
    """Return OK when placing *cmd.piece* at *cmd.position* is legal."""
    if state.phase is not GamePhase.SETUP:
        return ValidationResult.INVALID
    if cmd.piece.owner is not state.active_player:
        return ValidationResult.INVALID
    pos = cmd.position
    if not pos.is_valid():
        return ValidationResult.INVALID
    if state.board.is_lake(pos):
        return ValidationResult.INVALID
    if not state.board.is_in_setup_zone(pos, cmd.piece.owner):
        return ValidationResult.INVALID
    if not state.board.is_empty(pos):
        return ValidationResult.INVALID
    return ValidationResult.OK


def apply_placement(state: GameState, cmd: PlacementCommand) -> GameState:
    """Apply *cmd* to *state* and return the updated state.

    Raises :class:`RulesViolationError` when the placement is illegal.
    """
    if validate_placement(state, cmd) is ValidationResult.INVALID:
        raise RulesViolationError(
            f"Invalid placement of {cmd.piece.rank} at {cmd.position}"
        )
    new_board = state.board.place_piece(cmd.piece, cmd.position)
    new_players = _update_player_pieces(state, cmd.piece)
    return dataclasses.replace(state, board=new_board, players=new_players)


def is_setup_complete(state: GameState) -> bool:
    """Return True when both players have placed all 40 pieces."""
    for player in state.players:
        count = sum(
            1
            for sq in state.board.squares.values()
            if sq.piece is not None and sq.piece.owner is player.side
        )
        if count < _PIECES_PER_SIDE:
            return False
    return True


# ---------------------------------------------------------------------------
# Move validation (playing phase)
# ---------------------------------------------------------------------------


def validate_move(state: GameState, move: Move) -> ValidationResult:
    """Return OK when *move* is fully legal in the current *state*."""
    if state.phase is not GamePhase.PLAYING:
        return ValidationResult.INVALID

    piece = move.piece
    if piece.owner is not state.active_player:
        return ValidationResult.INVALID

    # Immovable pieces
    if piece.rank in (Rank.BOMB, Rank.FLAG):
        return ValidationResult.INVALID

    from_pos, to_pos = move.from_pos, move.to_pos
    if from_pos == to_pos:
        return ValidationResult.INVALID

    row_delta = abs(to_pos.row - from_pos.row)
    col_delta = abs(to_pos.col - from_pos.col)

    # Diagonal move
    if row_delta > 0 and col_delta > 0:
        return ValidationResult.INVALID

    # Destination must be in bounds
    if not to_pos.is_valid():
        return ValidationResult.INVALID

    # Destination must not be a lake
    if state.board.is_lake(to_pos):
        return ValidationResult.INVALID

    # Destination must not hold a friendly piece
    dest_square = state.board.get_square(to_pos)
    if dest_square.piece is not None and dest_square.piece.owner is piece.owner:
        return ValidationResult.INVALID

    distance = row_delta + col_delta

    if piece.rank is Rank.SCOUT:
        # Scout may move any number of squares along a straight line
        if not _scout_path_clear(state.board, from_pos, to_pos, piece.owner):
            return ValidationResult.INVALID
    else:
        if distance > 1:
            return ValidationResult.INVALID

    # Two-square rule
    if _violates_two_square_rule(state, move):
        return ValidationResult.INVALID

    return ValidationResult.OK


def apply_move(state: GameState, move: Move) -> GameState:
    """Apply *move* to *state* and return the updated ``GameState``.

    Raises :class:`RulesViolationError` when the move is illegal.
    """
    if validate_move(state, move) is ValidationResult.INVALID:
        raise RulesViolationError(f"Invalid move: {move}")

    dest_square = state.board.get_square(move.to_pos)
    board = state.board

    combat_result = None
    if dest_square.piece is not None:
        # Attack
        combat_result = resolve_combat(move.piece, dest_square.piece)
        board = _apply_combat_to_board(board, move, combat_result)
    else:
        board = board.move_piece(move.from_pos, move.to_pos)

    import time

    record = MoveRecord(
        move=move,
        combat_result=combat_result,
        turn_number=state.turn_number,
        timestamp=time.time(),
    )
    new_history = state.move_history + (record,)

    # Switch active player
    next_player = _other_side(state.active_player)
    new_turn = state.turn_number + 1

    # Update player snapshots
    new_players = _rebuild_players(state, board)

    new_state = dataclasses.replace(
        state,
        board=board,
        players=new_players,
        active_player=next_player,
        turn_number=new_turn,
        move_history=new_history,
    )
    return check_win_condition(new_state)


# ---------------------------------------------------------------------------
# Move generation
# ---------------------------------------------------------------------------


def generate_moves(state: GameState, player_side: PlayerSide) -> list[Move]:
    """Return every legal move available to *player_side* in *state*."""
    moves: list[Move] = []
    for square in state.board.squares.values():
        piece = square.piece
        if piece is None or piece.owner is not player_side:
            continue
        if piece.rank in (Rank.BOMB, Rank.FLAG):
            continue
        for candidate in _candidate_destinations(state.board, square.position, piece):
            move_type = (
                MoveType.ATTACK
                if state.board.get_square(candidate).piece is not None
                else MoveType.MOVE
            )
            move = Move(
                piece=piece,
                from_pos=square.position,
                to_pos=candidate,
                move_type=move_type,
            )
            if validate_move(state, move) is ValidationResult.OK:
                moves.append(move)
    return moves


# ---------------------------------------------------------------------------
# Win condition
# ---------------------------------------------------------------------------


def check_win_condition(state: GameState) -> GameState:
    """Return *state* updated to GAME_OVER if a terminal condition is met.

    Terminal conditions (checked in order):
    1. A player's flag has been captured (flag square is empty).
    2. A player has no movable pieces remaining.
    3. Turn number reached :data:`_MAX_TURNS` (draw – ``winner=None``).
    """
    # Check flag capture
    for player in state.players:
        flag_pos = player.flag_position
        if flag_pos is not None:
            sq = state.board.get_square(flag_pos)
            if sq.piece is None or sq.piece.rank is not Rank.FLAG:
                # Flag was captured – opponent wins
                winner = _other_side(player.side)
                return dataclasses.replace(state, phase=GamePhase.GAME_OVER, winner=winner)

    # Check draw by turn limit
    if state.turn_number >= _MAX_TURNS:
        return dataclasses.replace(state, phase=GamePhase.GAME_OVER, winner=None)

    # Check whether the active player has any legal moves
    active_moves = generate_moves(state, state.active_player)
    if not active_moves:
        winner = _other_side(state.active_player)
        return dataclasses.replace(state, phase=GamePhase.GAME_OVER, winner=winner)

    return state


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


class PlacementCommand:
    """Value object carrying the data needed to place a piece during setup."""

    def __init__(self, piece: Piece, position: Position) -> None:
        """Initialise a placement command."""
        self.piece = piece
        self.position = position


def _other_side(side: PlayerSide) -> PlayerSide:
    """Return the opposing side."""
    return PlayerSide.BLUE if side is PlayerSide.RED else PlayerSide.RED


def _scout_path_clear(
    board: Board, from_pos: Position, to_pos: Position, owner: PlayerSide
) -> bool:
    """Return True when the Scout's path is unobstructed.

    A Scout may pass through empty squares but may not:
    - pass through a lake square,
    - pass through a friendly piece,
    - jump over an enemy piece (it may stop on the enemy square to attack).
    """
    row_step = _sign(to_pos.row - from_pos.row)
    col_step = _sign(to_pos.col - from_pos.col)

    current_row = from_pos.row + row_step
    current_col = from_pos.col + col_step

    while (current_row, current_col) != (to_pos.row, to_pos.col):
        intermediate = Position(current_row, current_col)
        sq = board.get_square(intermediate)
        if sq.terrain is TerrainType.LAKE:
            return False
        if sq.piece is not None:
            # Any piece in the path (friendly or enemy) blocks further travel
            return False
        current_row += row_step
        current_col += col_step

    # Final destination checks already done by caller
    dest_sq = board.get_square(to_pos)
    if dest_sq.terrain is TerrainType.LAKE:
        return False
    if dest_sq.piece is not None and dest_sq.piece.owner is owner:
        return False
    return True


def _sign(n: int) -> int:
    """Return the arithmetic sign of *n* as -1, 0, or 1."""
    if n > 0:
        return 1
    if n < 0:
        return -1
    return 0


def _violates_two_square_rule(state: GameState, move: Move) -> bool:
    """Return True when *move* would complete a second full round-trip oscillation.

    The two-square rule forbids a piece from bouncing between the same two
    squares forever.  We reject a move when the same piece has already made
    the same from→to trip at least twice in immediately preceding moves
    (i.e., the move_history tail shows A→B, B→A, A→B for the same piece).
    """
    history = state.move_history
    # We need at least 3 previous moves for the same piece to detect a
    # second round-trip.  Collect recent moves for this piece.
    same_piece_moves: list[tuple[Position, Position]] = []
    for record in reversed(history):
        rec_move = record.move
        if rec_move.piece.rank == move.piece.rank and rec_move.piece.owner == move.piece.owner:
            same_piece_moves.append((rec_move.from_pos, rec_move.to_pos))
            if len(same_piece_moves) >= 4:
                break

    # Pattern to detect: ...A→B, B→A, A→B (about to become 4th trip B→A or 3rd A→B)
    # Simplified: if last two moves for this piece are B→A and A→B (i.e., the reverse
    # of the current move and the current move itself), reject a third repetition.
    if len(same_piece_moves) >= 2:
        prev1_from, prev1_to = same_piece_moves[0]  # most recent
        prev2_from, prev2_to = same_piece_moves[1]  # second most recent
        # Would this move create a third oscillation?  Pattern: X→Y, Y→X, X→Y
        if (
            prev2_from == move.from_pos
            and prev2_to == move.to_pos
            and prev1_from == move.to_pos
            and prev1_to == move.from_pos
        ):
            return True
    return False


def _candidate_destinations(
    board: Board, from_pos: Position, piece: Piece
) -> list[Position]:
    """Return raw destination candidates (without full legality check)."""
    if piece.rank is Rank.SCOUT:
        candidates: list[Position] = []
        for d_row, d_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            r, c = from_pos.row + d_row, from_pos.col + d_col
            while 0 <= r <= 9 and 0 <= c <= 9:
                pos = Position(r, c)
                sq = board.get_square(pos)
                if sq.terrain is TerrainType.LAKE:
                    break
                if sq.piece is not None:
                    if sq.piece.owner is not piece.owner:
                        candidates.append(pos)
                    break
                candidates.append(pos)
                r += d_row
                c += d_col
        return candidates
    return board.neighbours(from_pos)


def _apply_combat_to_board(board: Board, move: Move, combat_result) -> Board:  # type: ignore[no-untyped-def]
    """Update *board* to reflect the result of combat at *move.to_pos*."""
    from src.domain.enums import CombatOutcome

    outcome = combat_result.outcome
    if outcome is CombatOutcome.ATTACKER_WINS:
        board = board.remove_piece(move.from_pos)
        # Place revealed attacker at destination
        revealed = combat_result.attacker
        dest_sq = board.get_square(move.to_pos)
        from src.domain.square import Square

        new_squares = dict(board.squares)
        new_squares[move.to_pos] = Square(
            position=move.to_pos,
            piece=Piece(
                rank=revealed.rank,
                owner=revealed.owner,
                revealed=True,
                has_moved=True,
                position=move.to_pos,
            ),
            terrain=dest_sq.terrain,
        )
        return Board(squares=new_squares)
    elif outcome is CombatOutcome.DEFENDER_WINS:
        board = board.remove_piece(move.from_pos)
        # Defender stays (revealed) at its position
        def_sq = board.get_square(move.to_pos)
        from src.domain.square import Square

        new_squares = dict(board.squares)
        new_squares[move.to_pos] = Square(
            position=move.to_pos,
            piece=Piece(
                rank=def_sq.piece.rank,  # type: ignore[union-attr]
                owner=def_sq.piece.owner,  # type: ignore[union-attr]
                revealed=True,
                has_moved=def_sq.piece.has_moved,  # type: ignore[union-attr]
                position=move.to_pos,
            ),
            terrain=def_sq.terrain,
        )
        return Board(squares=new_squares)
    else:
        # DRAW – remove both
        board = board.remove_piece(move.from_pos)
        board = board.remove_piece(move.to_pos)
        return board


def _update_player_pieces(state: GameState, new_piece: Piece) -> tuple[Player, Player]:
    """Return updated players tuple after a piece has been placed on the board."""
    updated: list[Player] = []
    for player in state.players:
        if player.side is new_piece.owner:
            updated.append(
                Player(
                    side=player.side,
                    player_type=player.player_type,
                    pieces_remaining=player.pieces_remaining + (new_piece,),
                    flag_position=(
                        new_piece.position if new_piece.rank is Rank.FLAG else player.flag_position
                    ),
                )
            )
        else:
            updated.append(player)
    return (updated[0], updated[1])


def _rebuild_players(state: GameState, board: Board) -> tuple[Player, Player]:
    """Rebuild player snapshots from the current board after a move."""
    result: list[Player] = []
    for player in state.players:
        pieces = tuple(
            sq.piece
            for sq in board.squares.values()
            if sq.piece is not None and sq.piece.owner is player.side
        )
        flag_pos: Position | None = None
        for p in pieces:
            if p.rank is Rank.FLAG:
                flag_pos = p.position
                break
        result.append(
            Player(
                side=player.side,
                player_type=player.player_type,
                pieces_remaining=pieces,
                flag_position=flag_pos,
            )
        )
    return (result[0], result[1])
