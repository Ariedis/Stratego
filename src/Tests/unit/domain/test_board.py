"""
test_board.py — Unit tests for src/domain/board.py

Epic: EPIC-2 | User Story: US-201
Covers acceptance criteria: AC-1 through AC-5
Specification: game_components.md §2 (Board), data_models.md §3.6
"""
from __future__ import annotations

import pytest

from src.domain.board import Board
from src.domain.enums import PlayerSide, Rank, TerrainType
from src.domain.piece import Position
from src.Tests.fixtures.sample_game_states import make_blue_piece, make_red_piece

# ---------------------------------------------------------------------------
# US-201 AC-1: Exactly 8 lake squares at the correct positions
# ---------------------------------------------------------------------------


LAKE_POSITIONS: list[tuple[int, int]] = [
    (4, 2), (4, 3), (5, 2), (5, 3),
    (4, 6), (4, 7), (5, 6), (5, 7),
]

NON_LAKE_POSITIONS: list[tuple[int, int]] = [
    (0, 0), (0, 9), (9, 0), (9, 9),
    (4, 4), (5, 5), (3, 2), (6, 6),
]


class TestBoardLakes:
    """AC-1: Board must have exactly 8 lake squares at the canonical positions."""

    @pytest.mark.parametrize("row,col", LAKE_POSITIONS)
    def test_lake_square_is_identified(self, empty_board: Board, row: int, col: int) -> None:
        """Every canonical lake position must be recognised as a lake."""
        assert empty_board.is_lake(Position(row, col)) is True

    @pytest.mark.parametrize("row,col", NON_LAKE_POSITIONS)
    def test_non_lake_square_not_identified(
        self, empty_board: Board, row: int, col: int
    ) -> None:
        """Normal squares must not be identified as lakes."""
        assert empty_board.is_lake(Position(row, col)) is False

    def test_exactly_eight_lakes_exist(self, empty_board: Board) -> None:
        """The total lake count across the board must be exactly 8."""
        lake_count = sum(
            1
            for r in range(10)
            for c in range(10)
            if empty_board.is_lake(Position(r, c))
        )
        assert lake_count == 8

    def test_lake_squares_have_lake_terrain(self, empty_board: Board) -> None:
        """Lake squares must report terrain == TerrainType.LAKE."""
        for row, col in LAKE_POSITIONS:
            sq = empty_board.get_square(Position(row, col))
            assert sq.terrain == TerrainType.LAKE

    def test_non_lake_squares_have_normal_terrain(self, empty_board: Board) -> None:
        """Non-lake squares must report terrain == TerrainType.NORMAL."""
        for row, col in NON_LAKE_POSITIONS:
            sq = empty_board.get_square(Position(row, col))
            assert sq.terrain == TerrainType.NORMAL

    def test_user_story_example_lake_4_4_is_not_lake(self, empty_board: Board) -> None:
        """US-201 example: board.is_lake(Position(4, 4)) is False (between the two lakes)."""
        assert empty_board.is_lake(Position(4, 4)) is False


# ---------------------------------------------------------------------------
# US-201 AC-2: Neighbours of a central square
# ---------------------------------------------------------------------------


class TestBoardNeighbours:
    """AC-2 & AC-3: neighbours() returns the correct orthogonal adjacent positions."""

    def test_central_square_has_four_neighbours(self, empty_board: Board) -> None:
        """AC-2: Position(5,5) must have exactly 4 neighbours."""
        neighbours = empty_board.neighbours(Position(5, 5))
        assert len(neighbours) == 4

    def test_central_square_correct_neighbour_positions(self, empty_board: Board) -> None:
        """AC-2: Neighbours of (5,5) must be (4,5), (6,5), (5,4), (5,6)."""
        neighbours = set(empty_board.neighbours(Position(5, 5)))
        expected = {
            Position(4, 5),
            Position(6, 5),
            Position(5, 4),
            Position(5, 6),
        }
        assert neighbours == expected

    def test_corner_square_has_two_neighbours(self, empty_board: Board) -> None:
        """AC-3: Position(0,0) must have exactly 2 neighbours."""
        neighbours = empty_board.neighbours(Position(0, 0))
        assert len(neighbours) == 2

    def test_corner_square_correct_neighbour_positions(self, empty_board: Board) -> None:
        """AC-3: Neighbours of (0,0) must be (1,0) and (0,1)."""
        neighbours = set(empty_board.neighbours(Position(0, 0)))
        expected = {Position(1, 0), Position(0, 1)}
        assert neighbours == expected

    @pytest.mark.parametrize(
        "row,col,expected_count",
        [
            (0, 0, 2),   # corner
            (0, 5, 3),   # top edge
            (9, 0, 2),   # corner
            (9, 5, 3),   # bottom edge
            (5, 0, 3),   # left edge
            (5, 9, 3),   # right edge
            (5, 5, 4),   # interior
        ],
        ids=["top_left", "top_edge", "bottom_left", "bottom_edge",
             "left_edge", "right_edge", "interior"],
    )
    def test_neighbour_counts_at_boundary(
        self, empty_board: Board, row: int, col: int, expected_count: int
    ) -> None:
        """Neighbours must respect board boundaries."""
        neighbours = empty_board.neighbours(Position(row, col))
        assert len(neighbours) == expected_count

    def test_no_diagonal_neighbours(self, empty_board: Board) -> None:
        """Neighbours must be strictly orthogonal (no diagonals)."""
        neighbours = empty_board.neighbours(Position(5, 5))
        for n in neighbours:
            row_diff = abs(n.row - 5)
            col_diff = abs(n.col - 5)
            assert not (row_diff == 1 and col_diff == 1), f"Diagonal neighbour found: {n}"


# ---------------------------------------------------------------------------
# US-201 AC-4 & AC-5: Setup zone boundaries
# ---------------------------------------------------------------------------


class TestSetupZone:
    """AC-4 & AC-5: is_in_setup_zone() correctly identifies player setup zones."""

    @pytest.mark.parametrize(
        "row,col,side,expected",
        [
            # RED zones (rows 6–9)
            (6, 0, PlayerSide.RED, True),
            (7, 3, PlayerSide.RED, True),
            (8, 5, PlayerSide.RED, True),
            (9, 9, PlayerSide.RED, True),
            (5, 0, PlayerSide.RED, False),  # row 5 is not in RED's zone
            (4, 3, PlayerSide.RED, False),  # AC-5: row 4 is not RED's zone
            # BLUE zones (rows 0–3)
            (0, 0, PlayerSide.BLUE, True),
            (1, 5, PlayerSide.BLUE, True),
            (2, 9, PlayerSide.BLUE, True),
            (3, 3, PlayerSide.BLUE, True),
            (4, 0, PlayerSide.BLUE, False),  # row 4 is not in BLUE's zone
            (9, 9, PlayerSide.BLUE, False),  # RED's zone
        ],
        ids=[
            "red_row6", "red_row7_ac4", "red_row8", "red_row9",
            "red_row5_invalid", "red_row4_invalid_ac5",
            "blue_row0", "blue_row1", "blue_row2", "blue_row3",
            "blue_row4_invalid", "blue_row9_invalid",
        ],
    )
    def test_setup_zone(
        self, empty_board: Board, row: int, col: int, side: PlayerSide, expected: bool
    ) -> None:
        assert empty_board.is_in_setup_zone(Position(row, col), side) is expected


# ---------------------------------------------------------------------------
# Board mutability (place/remove pieces — returns new Board)
# ---------------------------------------------------------------------------


class TestBoardPiecePlacement:
    """Board.place_piece() returns a new board; original is unchanged (immutability)."""

    def test_place_piece_adds_piece_to_square(self, empty_board: Board) -> None:
        piece = make_red_piece(Rank.SCOUT, 8, 3)
        new_board = empty_board.place_piece(piece)
        sq = new_board.get_square(Position(8, 3))
        assert sq.piece == piece

    def test_place_piece_does_not_mutate_original(self, empty_board: Board) -> None:
        piece = make_red_piece(Rank.MINER, 9, 1)
        _ = empty_board.place_piece(piece)
        sq = empty_board.get_square(Position(9, 1))
        assert sq.piece is None  # Original board is unchanged.

    def test_place_piece_on_lake_raises_value_error(self, empty_board: Board) -> None:
        lake_piece = make_red_piece(Rank.SCOUT, 4, 2)
        with pytest.raises(ValueError):
            empty_board.place_piece(lake_piece)

    def test_place_piece_on_occupied_square_raises_value_error(
        self, empty_board: Board
    ) -> None:
        piece_a = make_red_piece(Rank.SCOUT, 8, 0)
        piece_b = make_blue_piece(Rank.MINER, 8, 0)
        board_with_a = empty_board.place_piece(piece_a)
        with pytest.raises(ValueError, match="already occupied"):
            board_with_a.place_piece(piece_b)

    def test_remove_piece_clears_square(self, empty_board: Board) -> None:
        piece = make_red_piece(Rank.CAPTAIN, 7, 5)
        board_with_piece = empty_board.place_piece(piece)
        board_cleared = board_with_piece.remove_piece(piece.position)
        sq = board_cleared.get_square(piece.position)
        assert sq.piece is None

    def test_board_is_empty_after_empty_board_creation(self, empty_board: Board) -> None:
        """A freshly created board must have no pieces anywhere."""
        for (row, col), sq in empty_board.squares.items():
            assert sq.piece is None, f"Square ({row},{col}) unexpectedly has a piece"

    def test_place_piece_outside_board_raises_value_error(self, empty_board: Board) -> None:
        """Placing a piece at an off-board position raises ValueError."""
        piece = make_red_piece(Rank.SCOUT, -1, 0)
        with pytest.raises(ValueError):
            empty_board.place_piece(piece)

    def test_remove_piece_outside_board_raises_value_error(self, empty_board: Board) -> None:
        """Removing a piece at an off-board position raises ValueError."""
        with pytest.raises(ValueError):
            empty_board.remove_piece(Position(-1, 0))


# ---------------------------------------------------------------------------
# Board.is_empty() — not a lake, not occupied
# ---------------------------------------------------------------------------


class TestBoardIsEmpty:
    """Board.is_empty() returns True only for in-bounds, non-lake, unoccupied squares."""

    def test_empty_normal_square_is_empty(self, empty_board: Board) -> None:
        """A normal square with no piece is empty."""
        assert empty_board.is_empty(Position(5, 5)) is True

    def test_lake_square_is_not_empty(self, empty_board: Board) -> None:
        """A lake square is never considered empty."""
        assert empty_board.is_empty(Position(4, 2)) is False

    def test_occupied_square_is_not_empty(self, empty_board: Board) -> None:
        """A square with a piece on it is not empty."""
        piece = make_red_piece(Rank.SCOUT, 8, 3)
        board_with_piece = empty_board.place_piece(piece)
        assert board_with_piece.is_empty(Position(8, 3)) is False

    def test_out_of_bounds_position_is_not_empty(self, empty_board: Board) -> None:
        """An off-board position is not considered empty."""
        assert empty_board.is_empty(Position(-1, 0)) is False


# ---------------------------------------------------------------------------
# Board.move_piece() — TASK-201 step 9
# ---------------------------------------------------------------------------


class TestBoardMovePiece:
    """Board.move_piece() returns a new board with the piece relocated."""

    def test_move_piece_relocates_piece(self, empty_board: Board) -> None:
        """Moving a piece from (8,0) to (7,0) puts it at the new square."""
        piece = make_red_piece(Rank.SCOUT, 8, 0)
        board = empty_board.place_piece(piece)
        new_board = board.move_piece(piece.position, Position(7, 0))
        assert new_board.get_square(Position(7, 0)).piece is not None
        assert new_board.get_square(Position(8, 0)).piece is None

    def test_move_piece_sets_has_moved_true(self, empty_board: Board) -> None:
        """Moved piece has has_moved=True in the new board."""
        piece = make_red_piece(Rank.CAPTAIN, 8, 0)
        board = empty_board.place_piece(piece)
        new_board = board.move_piece(piece.position, Position(7, 0))
        moved = new_board.get_square(Position(7, 0)).piece
        assert moved is not None
        assert moved.has_moved is True

    def test_move_piece_updates_position(self, empty_board: Board) -> None:
        """Moved piece's .position attribute reflects the new square."""
        piece = make_red_piece(Rank.MAJOR, 8, 5)
        board = empty_board.place_piece(piece)
        new_board = board.move_piece(piece.position, Position(7, 5))
        moved = new_board.get_square(Position(7, 5)).piece
        assert moved is not None
        assert moved.position == Position(7, 5)

    def test_move_piece_returns_new_board(self, empty_board: Board) -> None:
        """move_piece() returns a new Board object (original unchanged)."""
        piece = make_red_piece(Rank.SCOUT, 8, 0)
        board = empty_board.place_piece(piece)
        new_board = board.move_piece(piece.position, Position(7, 0))
        assert new_board is not board
        assert board.get_square(Position(8, 0)).piece is not None

    def test_move_piece_no_piece_raises(self, empty_board: Board) -> None:
        """move_piece() raises ValueError if the source square is empty."""
        with pytest.raises(ValueError):
            empty_board.move_piece(Position(8, 0), Position(7, 0))

    def test_move_piece_invalid_from_pos_raises(self, empty_board: Board) -> None:
        """move_piece() raises ValueError for an out-of-bounds source position."""
        with pytest.raises(ValueError):
            empty_board.move_piece(Position(-1, 0), Position(0, 0))

    def test_move_piece_invalid_to_pos_raises(self, empty_board: Board) -> None:
        """move_piece() raises ValueError for an out-of-bounds destination position."""
        piece = make_red_piece(Rank.SCOUT, 8, 0)
        board = empty_board.place_piece(piece)
        with pytest.raises(ValueError):
            board.move_piece(piece.position, Position(-1, 0))
