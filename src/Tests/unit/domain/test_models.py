"""
test_models.py — Unit tests for core domain dataclasses.

Epic: EPIC-1 | User Story: US-103
Covers acceptance criteria: AC-1 through AC-5
Specification: data_models.md §2–§5 (Invariants I-1 through I-10)
"""
from __future__ import annotations

import pytest

from src.domain.board import Board
from src.domain.enums import GamePhase, PlayerSide, PlayerType, Rank
from src.domain.game_state import GameState
from src.domain.piece import Piece, Position
from src.domain.player import Player
from src.Tests.fixtures.sample_game_states import (
    make_blue_piece,
    make_empty_setup_state,
    make_red_piece,
)


# ---------------------------------------------------------------------------
# US-103 AC-1: Position validity
# ---------------------------------------------------------------------------


class TestPositionValidity:
    """AC-1: Position.is_valid() returns True for [0,9]×[0,9] only."""

    @pytest.mark.parametrize(
        "row,col,expected",
        [
            (5, 3, True),     # centre — valid
            (0, 0, True),     # top-left corner
            (9, 9, True),     # bottom-right corner
            (0, 9, True),     # top-right corner
            (9, 0, True),     # bottom-left corner
            (-1, 0, False),   # row below minimum
            (0, -1, False),   # col below minimum
            (10, 0, False),   # row above maximum
            (0, 10, False),   # col above maximum
            (-1, -1, False),  # both negative
            (10, 10, False),  # both out of range
        ],
        ids=[
            "centre", "top_left", "bottom_right", "top_right", "bottom_left",
            "neg_row", "neg_col", "row_too_large", "col_too_large",
            "both_negative", "both_too_large",
        ],
    )
    def test_position_is_valid(self, row: int, col: int, expected: bool) -> None:
        assert Position(row, col).is_valid() is expected

    def test_valid_position_from_user_story(self) -> None:
        """AC-1 example: Position(5, 3).is_valid() → True."""
        assert Position(row=5, col=3).is_valid() is True

    def test_invalid_negative_row(self) -> None:
        """AC-1 example: Position(-1, 0).is_valid() → False."""
        assert Position(row=-1, col=0).is_valid() is False


# ---------------------------------------------------------------------------
# US-103 AC-2: Piece immutability
# ---------------------------------------------------------------------------


class TestPieceImmutability:
    """AC-2: Pieces are frozen=True dataclasses; direct attribute mutation raises FrozenInstanceError."""

    def test_piece_is_immutable(self) -> None:
        """Attempting piece.revealed = True must raise FrozenInstanceError."""
        piece = Piece(
            rank=Rank.SCOUT,
            owner=PlayerSide.RED,
            revealed=False,
            has_moved=False,
            position=Position(6, 4),
        )
        with pytest.raises(Exception):  # FrozenInstanceError is a subclass of AttributeError
            piece.revealed = True  # type: ignore[misc]

    def test_position_is_immutable(self) -> None:
        pos = Position(3, 4)
        with pytest.raises(Exception):
            pos.row = 5  # type: ignore[misc]

    def test_piece_equality_by_value(self) -> None:
        """Two Pieces with identical fields must be equal (value object semantics)."""
        p1 = Piece(Rank.MINER, PlayerSide.RED, False, False, Position(7, 2))
        p2 = Piece(Rank.MINER, PlayerSide.RED, False, False, Position(7, 2))
        assert p1 == p2

    def test_piece_hashable(self) -> None:
        """Frozen dataclasses must be hashable (can be used in sets/dicts)."""
        piece = Piece(Rank.FLAG, PlayerSide.BLUE, False, False, Position(0, 0))
        assert hash(piece) == hash(piece)
        s = {piece}
        assert len(s) == 1


# ---------------------------------------------------------------------------
# US-103 AC-3: Board lake detection
# ---------------------------------------------------------------------------


class TestBoardLakeDetection:
    """AC-3: Board.is_lake() correctly identifies lake and non-lake positions."""

    def test_lake_position_4_2(self, empty_board: Board) -> None:
        assert empty_board.is_lake(Position(4, 2)) is True

    def test_non_lake_position_0_0(self, empty_board: Board) -> None:
        assert empty_board.is_lake(Position(0, 0)) is False

    def test_board_has_100_squares(self, empty_board: Board) -> None:
        assert len(empty_board.squares) == 100

    def test_user_story_example_lake(self, empty_board: Board) -> None:
        """AC-3 example: board.is_lake(Position(4, 2)) is True."""
        assert empty_board.is_lake(Position(4, 2)) is True

    def test_user_story_example_non_lake(self, empty_board: Board) -> None:
        """AC-3 example: board.is_lake(Position(0, 0)) is False."""
        assert empty_board.is_lake(Position(0, 0)) is False


# ---------------------------------------------------------------------------
# US-103 AC-4: Initial GameState is in SETUP phase
# ---------------------------------------------------------------------------


class TestInitialGameState:
    """AC-4: A freshly constructed GameState has phase == GamePhase.SETUP."""

    def test_initial_phase_is_setup(self, empty_setup_state: GameState) -> None:
        assert empty_setup_state.phase == GamePhase.SETUP

    def test_initial_active_player_is_red(self, empty_setup_state: GameState) -> None:
        """By convention, RED moves first (game_components.md §2.3)."""
        assert empty_setup_state.active_player == PlayerSide.RED

    def test_initial_turn_number_is_zero(self, empty_setup_state: GameState) -> None:
        assert empty_setup_state.turn_number == 0

    def test_initial_winner_is_none(self, empty_setup_state: GameState) -> None:
        """Invariant I-8: winner is None unless phase == GAME_OVER."""
        assert empty_setup_state.winner is None

    def test_initial_move_history_is_empty(self, empty_setup_state: GameState) -> None:
        assert len(empty_setup_state.move_history) == 0

    def test_initial_board_has_100_squares(self, empty_setup_state: GameState) -> None:
        assert len(empty_setup_state.board.squares) == 100

    def test_initial_state_has_two_players(self, empty_setup_state: GameState) -> None:
        assert len(empty_setup_state.players) == 2


# ---------------------------------------------------------------------------
# US-103 AC-5: GameState invariants
# ---------------------------------------------------------------------------


class TestGameStateInvariants:
    """AC-5: All 10 invariants from data_models.md §4 pass on a valid state."""

    def test_invariant_I1_all_positions_valid(self, empty_setup_state: GameState) -> None:
        """I-1: Every position in the board is within [0,9]×[0,9]."""
        for (row, col) in empty_setup_state.board.squares:
            assert Position(row, col).is_valid(), f"Position ({row},{col}) is invalid"

    def test_invariant_I2_no_two_pieces_same_position(self) -> None:
        """I-2: No two pieces may occupy the same Position."""
        board = Board.create_empty()
        piece_a = make_red_piece(Rank.SCOUT, 8, 0)
        piece_b = make_red_piece(Rank.MINER, 8, 0)  # Same position — should fail.
        board = board.place_piece(piece_a)
        with pytest.raises(ValueError, match="already occupied"):
            board.place_piece(piece_b)

    def test_invariant_I3_no_piece_on_lake(self) -> None:
        """I-3: A LAKE square never has a piece."""
        board = Board.create_empty()
        lake_piece = make_red_piece(Rank.SCOUT, 4, 2)
        with pytest.raises(ValueError):
            board.place_piece(lake_piece)

    def test_invariant_I8_winner_none_during_setup(self, empty_setup_state: GameState) -> None:
        """I-8: winner must be None when phase != GAME_OVER."""
        assert empty_setup_state.phase != GamePhase.GAME_OVER
        assert empty_setup_state.winner is None

    def test_invariant_I8_winner_only_in_game_over(self) -> None:
        """I-8: winner may only be set in GAME_OVER phase."""
        from dataclasses import replace

        state = make_empty_setup_state()
        game_over_state = replace(state, phase=GamePhase.GAME_OVER, winner=PlayerSide.RED)
        assert game_over_state.phase == GamePhase.GAME_OVER
        assert game_over_state.winner == PlayerSide.RED

    def test_invariant_I9_piece_position_matches_board(self) -> None:
        """I-9: piece.position equals the Position of the Square containing it."""
        piece = make_red_piece(Rank.SERGEANT, 7, 3)
        board = Board.create_empty()
        board = board.place_piece(piece)
        sq = board.get_square(piece.position)
        assert sq.piece is not None
        assert sq.piece.position == piece.position


# ---------------------------------------------------------------------------
# Player dataclass tests
# ---------------------------------------------------------------------------


class TestPlayerModel:
    """Player is a frozen dataclass with correct default values."""

    def test_player_immutable(self) -> None:
        player = Player(
            side=PlayerSide.RED,
            player_type=PlayerType.HUMAN,
        )
        with pytest.raises(Exception):
            player.side = PlayerSide.BLUE  # type: ignore[misc]

    def test_player_default_pieces_empty(self) -> None:
        player = Player(side=PlayerSide.BLUE, player_type=PlayerType.AI_EASY)
        assert len(player.pieces_remaining) == 0

    def test_player_flag_position_default_none(self) -> None:
        player = Player(side=PlayerSide.RED, player_type=PlayerType.HUMAN)
        assert player.flag_position is None
