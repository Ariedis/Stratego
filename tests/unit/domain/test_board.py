"""Unit tests for Board queries and immutable mutation methods."""

import pytest

from src.domain.board import LAKE_POSITIONS, Board
from src.domain.enums import PlayerSide, Rank, TerrainType
from src.domain.piece import Piece
from src.domain.position import Position


def _make_piece(rank: Rank = Rank.CAPTAIN, side: PlayerSide = PlayerSide.RED,
                pos: Position = Position(7, 0)) -> Piece:
    """Helper: create a minimal Piece for testing."""
    return Piece(rank=rank, owner=side, revealed=False, has_moved=False, position=pos)


class TestLakePositions:
    """Tests that all 8 expected lake squares are correctly identified."""

    def test_all_eight_lake_positions_are_lakes(self) -> None:
        """Every position in LAKE_POSITIONS is reported as a lake."""
        board = Board.create_empty()
        for pos in LAKE_POSITIONS:
            assert board.is_lake(pos), f"{pos} should be a lake"

    def test_non_lake_position_not_lake(self) -> None:
        """A normal square is not reported as a lake."""
        board = Board.create_empty()
        assert not board.is_lake(Position(0, 0))

    def test_eight_lake_positions_total(self) -> None:
        """LAKE_POSITIONS contains exactly 8 entries."""
        assert len(LAKE_POSITIONS) == 8

    def test_known_lake_positions(self) -> None:
        """The exact lake coordinates match the specification."""
        expected = {
            Position(4, 2), Position(4, 3), Position(5, 2), Position(5, 3),
            Position(4, 6), Position(4, 7), Position(5, 6), Position(5, 7),
        }
        assert LAKE_POSITIONS == expected


class TestNeighbours:
    """Tests for Board.neighbours() orthogonal adjacency."""

    def test_corner_has_two_neighbours(self) -> None:
        """The corner (0, 0) has exactly 2 valid neighbours."""
        board = Board.create_empty()
        assert len(board.neighbours(Position(0, 0))) == 2

    def test_edge_has_three_neighbours(self) -> None:
        """A non-corner edge square (0, 5) has exactly 3 valid neighbours."""
        board = Board.create_empty()
        assert len(board.neighbours(Position(0, 5))) == 3

    def test_centre_has_four_neighbours(self) -> None:
        """An interior square (5, 5) has exactly 4 valid neighbours."""
        board = Board.create_empty()
        assert len(board.neighbours(Position(5, 5))) == 4

    def test_neighbours_are_orthogonal(self) -> None:
        """All neighbours of (3, 3) differ by exactly 1 in row or col (not both)."""
        board = Board.create_empty()
        pos = Position(3, 3)
        for n in board.neighbours(pos):
            row_diff = abs(n.row - pos.row)
            col_diff = abs(n.col - pos.col)
            assert row_diff + col_diff == 1


class TestSetupZone:
    """Tests for Board.is_in_setup_zone()."""

    def test_red_row_9_in_zone(self) -> None:
        """Row 9 is inside RED's setup zone."""
        board = Board.create_empty()
        assert board.is_in_setup_zone(Position(9, 0), PlayerSide.RED)

    def test_red_row_6_in_zone(self) -> None:
        """Row 6 is inside RED's setup zone."""
        board = Board.create_empty()
        assert board.is_in_setup_zone(Position(6, 0), PlayerSide.RED)

    def test_red_row_5_not_in_zone(self) -> None:
        """Row 5 is outside RED's setup zone."""
        board = Board.create_empty()
        assert not board.is_in_setup_zone(Position(5, 0), PlayerSide.RED)

    def test_blue_row_0_in_zone(self) -> None:
        """Row 0 is inside BLUE's setup zone."""
        board = Board.create_empty()
        assert board.is_in_setup_zone(Position(0, 0), PlayerSide.BLUE)

    def test_blue_row_3_in_zone(self) -> None:
        """Row 3 is inside BLUE's setup zone."""
        board = Board.create_empty()
        assert board.is_in_setup_zone(Position(3, 0), PlayerSide.BLUE)

    def test_blue_row_4_not_in_zone(self) -> None:
        """Row 4 is outside BLUE's setup zone."""
        board = Board.create_empty()
        assert not board.is_in_setup_zone(Position(4, 0), PlayerSide.BLUE)


class TestPlacePiece:
    """Tests for Board.place_piece() immutability and correctness."""

    def test_place_piece_returns_new_board(self) -> None:
        """place_piece returns a different Board instance."""
        board = Board.create_empty()
        piece = _make_piece(pos=Position(7, 0))
        new_board = board.place_piece(piece, Position(7, 0))
        assert new_board is not board

    def test_original_board_unchanged(self) -> None:
        """The original board still has no piece after place_piece."""
        board = Board.create_empty()
        piece = _make_piece(pos=Position(7, 0))
        _ = board.place_piece(piece, Position(7, 0))
        assert board.get_square(Position(7, 0)).piece is None

    def test_new_board_has_piece(self) -> None:
        """The new board contains the placed piece at the correct square."""
        board = Board.create_empty()
        piece = _make_piece(pos=Position(7, 0))
        new_board = board.place_piece(piece, Position(7, 0))
        assert new_board.get_square(Position(7, 0)).piece == piece

    def test_terrain_preserved_after_placement(self) -> None:
        """Placing a piece does not change the square's terrain."""
        board = Board.create_empty()
        pos = Position(7, 0)
        piece = _make_piece(pos=pos)
        new_board = board.place_piece(piece, pos)
        assert new_board.get_square(pos).terrain is TerrainType.NORMAL


class TestMovePiece:
    """Tests for Board.move_piece() correctness."""

    def test_move_piece_updates_destination(self) -> None:
        """After move_piece, the destination square contains the (moved) piece."""
        board = Board.create_empty()
        from_pos = Position(7, 0)
        to_pos = Position(6, 0)
        piece = _make_piece(pos=from_pos)
        board = board.place_piece(piece, from_pos)
        new_board = board.move_piece(from_pos, to_pos)
        dest_piece = new_board.get_square(to_pos).piece
        assert dest_piece is not None
        assert dest_piece.rank is piece.rank

    def test_move_piece_clears_source(self) -> None:
        """After move_piece, the source square is empty."""
        board = Board.create_empty()
        from_pos = Position(7, 0)
        to_pos = Position(6, 0)
        piece = _make_piece(pos=from_pos)
        board = board.place_piece(piece, from_pos)
        new_board = board.move_piece(from_pos, to_pos)
        assert new_board.get_square(from_pos).piece is None

    def test_move_piece_sets_has_moved(self) -> None:
        """The moved piece has has_moved=True on the destination square."""
        board = Board.create_empty()
        from_pos = Position(7, 0)
        to_pos = Position(6, 0)
        piece = _make_piece(pos=from_pos)
        board = board.place_piece(piece, from_pos)
        new_board = board.move_piece(from_pos, to_pos)
        assert new_board.get_square(to_pos).piece is not None
        assert new_board.get_square(to_pos).piece.has_moved is True  # type: ignore[union-attr]

    def test_move_piece_no_piece_raises(self) -> None:
        """move_piece raises ValueError when no piece is at from_pos."""
        board = Board.create_empty()
        with pytest.raises(ValueError):
            board.move_piece(Position(7, 0), Position(6, 0))


class TestRemovePiece:
    """Tests for Board.remove_piece()."""

    def test_remove_piece_clears_square(self) -> None:
        """After remove_piece the square is empty."""
        board = Board.create_empty()
        pos = Position(7, 0)
        piece = _make_piece(pos=pos)
        board = board.place_piece(piece, pos)
        new_board = board.remove_piece(pos)
        assert new_board.get_square(pos).piece is None

    def test_remove_preserves_terrain(self) -> None:
        """Removing a piece does not change the square's terrain."""
        board = Board.create_empty()
        pos = Position(7, 0)
        piece = _make_piece(pos=pos)
        board = board.place_piece(piece, pos)
        new_board = board.remove_piece(pos)
        assert new_board.get_square(pos).terrain is TerrainType.NORMAL
