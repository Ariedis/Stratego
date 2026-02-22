"""Unit tests for core domain value-object dataclasses."""

import pytest

from src.domain.board import Board
from src.domain.enums import PlayerSide, PlayerType, Rank, TerrainType
from src.domain.piece import Piece
from src.domain.player import Player
from src.domain.position import Position


class TestPosition:
    """Tests for Position.is_valid() boundary conditions."""

    def test_origin_valid(self) -> None:
        """(0, 0) is inside the board."""
        assert Position(0, 0).is_valid()

    def test_far_corner_valid(self) -> None:
        """(9, 9) is inside the board."""
        assert Position(9, 9).is_valid()

    def test_negative_row_invalid(self) -> None:
        """(-1, 0) is outside the board."""
        assert not Position(-1, 0).is_valid()

    def test_row_ten_invalid(self) -> None:
        """(10, 0) is outside the board."""
        assert not Position(10, 0).is_valid()

    def test_negative_col_invalid(self) -> None:
        """(0, -1) is outside the board."""
        assert not Position(0, -1).is_valid()

    def test_col_ten_invalid(self) -> None:
        """(0, 10) is outside the board."""
        assert not Position(0, 10).is_valid()

    def test_middle_valid(self) -> None:
        """(5, 5) is inside the board."""
        assert Position(5, 5).is_valid()


class TestPiece:
    """Tests for Piece immutability."""

    def _make_piece(self) -> Piece:
        """Create a sample piece for testing."""
        return Piece(
            rank=Rank.CAPTAIN,
            owner=PlayerSide.RED,
            revealed=False,
            has_moved=False,
            position=Position(7, 0),
        )

    def test_piece_is_frozen(self) -> None:
        """Attempting to mutate a Piece raises FrozenInstanceError."""
        piece = self._make_piece()
        with pytest.raises(Exception):  # FrozenInstanceError is a subclass of AttributeError
            piece.revealed = True  # type: ignore[misc]

    def test_piece_attributes(self) -> None:
        """Piece stores its fields correctly."""
        piece = self._make_piece()
        assert piece.rank is Rank.CAPTAIN
        assert piece.owner is PlayerSide.RED
        assert piece.revealed is False
        assert piece.has_moved is False
        assert piece.position == Position(7, 0)


class TestBoard:
    """Tests for Board.create_empty() and basic invariants."""

    def test_create_empty_has_100_squares(self) -> None:
        """A freshly created board contains exactly 100 squares."""
        board = Board.create_empty()
        assert len(board.squares) == 100

    def test_create_empty_has_eight_lake_squares(self) -> None:
        """Exactly 8 squares are terrain LAKE on an empty board."""
        board = Board.create_empty()
        lake_count = sum(
            1 for sq in board.squares.values() if sq.terrain is TerrainType.LAKE
        )
        assert lake_count == 8

    def test_create_empty_no_pieces(self) -> None:
        """No pieces are present on a freshly created board."""
        board = Board.create_empty()
        for sq in board.squares.values():
            assert sq.piece is None

    def test_all_squares_have_matching_position_key(self) -> None:
        """Each square's position equals its dict key."""
        board = Board.create_empty()
        for pos, sq in board.squares.items():
            assert sq.position == pos


class TestPlayer:
    """Tests for the Player dataclass invariants."""

    def test_player_is_frozen(self) -> None:
        """Attempting to mutate a Player raises FrozenInstanceError."""
        player = Player(
            side=PlayerSide.RED,
            player_type=PlayerType.HUMAN,
            pieces_remaining=(),
            flag_position=None,
        )
        with pytest.raises(Exception):
            player.side = PlayerSide.BLUE  # type: ignore[misc]
