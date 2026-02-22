"""Factory functions providing reusable sample game states for tests."""

from __future__ import annotations

from src.domain.board import Board
from src.domain.enums import GamePhase, PlayerSide, PlayerType, Rank
from src.domain.game_state import GameState
from src.domain.piece import Piece
from src.domain.player import Player
from src.domain.position import Position


def make_empty_board() -> Board:
    """Return a fresh 10×10 board with no pieces and correct lake terrain."""
    return Board.create_empty()


def make_initial_game_state() -> GameState:
    """Return a GameState in SETUP phase with no pieces placed.

    Both players are human and have empty piece rosters.
    """
    board = Board.create_empty()
    red_player = Player(
        side=PlayerSide.RED,
        player_type=PlayerType.HUMAN,
        pieces_remaining=(),
        flag_position=None,
    )
    blue_player = Player(
        side=PlayerSide.BLUE,
        player_type=PlayerType.HUMAN,
        pieces_remaining=(),
        flag_position=None,
    )
    return GameState(
        board=board,
        players=(red_player, blue_player),
        active_player=PlayerSide.RED,
        phase=GamePhase.SETUP,
        turn_number=0,
        move_history=(),
        winner=None,
    )


def make_playing_state() -> GameState:
    """Return a GameState in PLAYING phase with 10 pieces per side.

    Red pieces occupy rows 6–7 (col 0–4); blue pieces occupy rows 2–3 (col 0–4).
    Each side has one Flag, one Bomb, and eight mobile pieces.
    """
    _RED_RANKS = [
        Rank.FLAG, Rank.BOMB, Rank.MARSHAL, Rank.GENERAL,
        Rank.COLONEL, Rank.MAJOR, Rank.CAPTAIN, Rank.LIEUTENANT,
        Rank.SERGEANT, Rank.MINER,
    ]
    _BLUE_RANKS = [
        Rank.FLAG, Rank.BOMB, Rank.MARSHAL, Rank.GENERAL,
        Rank.COLONEL, Rank.MAJOR, Rank.CAPTAIN, Rank.LIEUTENANT,
        Rank.SERGEANT, Rank.MINER,
    ]

    board = Board.create_empty()
    red_pieces: list[Piece] = []
    blue_pieces: list[Piece] = []

    for i, rank in enumerate(_RED_RANKS):
        row = 6 + i // 5
        col = i % 5
        pos = Position(row, col)
        piece = Piece(rank=rank, owner=PlayerSide.RED, revealed=False,
                      has_moved=False, position=pos)
        board = board.place_piece(piece, pos)
        red_pieces.append(piece)

    for i, rank in enumerate(_BLUE_RANKS):
        row = 2 + i // 5
        col = i % 5
        pos = Position(row, col)
        piece = Piece(rank=rank, owner=PlayerSide.BLUE, revealed=False,
                      has_moved=False, position=pos)
        board = board.place_piece(piece, pos)
        blue_pieces.append(piece)

    red_flag_pos = next(p.position for p in red_pieces if p.rank is Rank.FLAG)
    blue_flag_pos = next(p.position for p in blue_pieces if p.rank is Rank.FLAG)

    red_player = Player(
        side=PlayerSide.RED,
        player_type=PlayerType.HUMAN,
        pieces_remaining=tuple(red_pieces),
        flag_position=red_flag_pos,
    )
    blue_player = Player(
        side=PlayerSide.BLUE,
        player_type=PlayerType.HUMAN,
        pieces_remaining=tuple(blue_pieces),
        flag_position=blue_flag_pos,
    )
    return GameState(
        board=board,
        players=(red_player, blue_player),
        active_player=PlayerSide.RED,
        phase=GamePhase.PLAYING,
        turn_number=1,
        move_history=(),
        winner=None,
    )
