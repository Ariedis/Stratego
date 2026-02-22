"""
src/Tests/fixtures/sample_game_states.py

Factory functions for creating representative GameState objects for use
in unit and integration tests.

Usage:
    from src.Tests.fixtures.sample_game_states import make_empty_setup_state
    state = make_empty_setup_state()
"""
from __future__ import annotations

from src.domain.board import Board
from src.domain.enums import GamePhase, PlayerSide, PlayerType, Rank
from src.domain.game_state import GameState
from src.domain.piece import Piece, Position
from src.domain.player import Player

# ---------------------------------------------------------------------------
# Piece factory helpers
# ---------------------------------------------------------------------------


def make_piece(
    rank: Rank,
    owner: PlayerSide,
    row: int,
    col: int,
    *,
    revealed: bool = False,
    has_moved: bool = False,
) -> Piece:
    """Create a Piece at (row, col) with sensible defaults for testing."""
    return Piece(
        rank=rank,
        owner=owner,
        revealed=revealed,
        has_moved=has_moved,
        position=Position(row, col),
    )


def make_red_piece(rank: Rank, row: int, col: int, **kwargs: bool) -> Piece:
    """Convenience: create a RED piece."""
    return make_piece(rank, PlayerSide.RED, row, col, **kwargs)


def make_blue_piece(rank: Rank, row: int, col: int, **kwargs: bool) -> Piece:
    """Convenience: create a BLUE piece."""
    return make_piece(rank, PlayerSide.BLUE, row, col, **kwargs)


# ---------------------------------------------------------------------------
# Player factory helpers
# ---------------------------------------------------------------------------


def make_human_player(side: PlayerSide, pieces: tuple[Piece, ...] = ()) -> Player:
    """Create a human Player with the given pieces."""
    flag_pos = next(
        (p.position for p in pieces if p.rank == Rank.FLAG), None
    )
    return Player(
        side=side,
        player_type=PlayerType.HUMAN,
        pieces_remaining=pieces,
        flag_position=flag_pos,
    )


# ---------------------------------------------------------------------------
# State factories
# ---------------------------------------------------------------------------


def make_empty_setup_state() -> GameState:
    """Return a GameState in SETUP phase with an empty board and no pieces placed."""
    board = Board.create_empty()
    red_player = make_human_player(PlayerSide.RED)
    blue_player = make_human_player(PlayerSide.BLUE)
    return GameState(
        board=board,
        players=(red_player, blue_player),
        active_player=PlayerSide.RED,
        phase=GamePhase.SETUP,
        turn_number=0,
    )


def make_minimal_playing_state(
    red_pieces: list[Piece] | None = None,
    blue_pieces: list[Piece] | None = None,
) -> GameState:
    """Return a PLAYING GameState with specified pieces on the board.

    Default: each player has one Flag and one Scout for minimal viable state.
    """
    if red_pieces is None:
        red_pieces = [
            make_red_piece(Rank.FLAG, 9, 0),
            make_red_piece(Rank.SCOUT, 8, 0),
        ]
    if blue_pieces is None:
        blue_pieces = [
            make_blue_piece(Rank.FLAG, 0, 0),
            make_blue_piece(Rank.SCOUT, 1, 0),
        ]

    board = Board.create_empty()
    for p in red_pieces + blue_pieces:
        board = board.place_piece(p)

    red_player = make_human_player(PlayerSide.RED, tuple(red_pieces))
    blue_player = make_human_player(PlayerSide.BLUE, tuple(blue_pieces))

    return GameState(
        board=board,
        players=(red_player, blue_player),
        active_player=PlayerSide.RED,
        phase=GamePhase.PLAYING,
        turn_number=1,
    )


def make_combat_state(
    attacker: Piece,
    defender: Piece,
) -> GameState:
    """Return a minimal PLAYING GameState with exactly two pieces on the board."""
    board = Board.create_empty()
    board = board.place_piece(attacker)
    board = board.place_piece(defender)

    red_pieces = (attacker,) if attacker.owner == PlayerSide.RED else (defender,)
    blue_pieces = (defender,) if defender.owner == PlayerSide.BLUE else (attacker,)

    # Ensure each side has a flag piece for win-condition compliance.
    red_flag = make_red_piece(Rank.FLAG, 9, 9)
    blue_flag = make_blue_piece(Rank.FLAG, 0, 9)
    board = board.place_piece(red_flag)
    board = board.place_piece(blue_flag)

    red_player = make_human_player(PlayerSide.RED, red_pieces + (red_flag,))
    blue_player = make_human_player(PlayerSide.BLUE, blue_pieces + (blue_flag,))

    return GameState(
        board=board,
        players=(red_player, blue_player),
        active_player=PlayerSide.RED,
        phase=GamePhase.PLAYING,
        turn_number=1,
    )
