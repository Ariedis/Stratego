"""
src/domain/board.py

Immutable 10×10 Board model with lake squares, neighbour queries, and
setup-zone boundaries.
Specification: game_components.md §2, data_models.md §2 (Board entity)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.enums import PlayerSide, TerrainType
from src.domain.piece import Piece, Position

# Lake positions defined by the official Stratego rules.
# game_components.md §2.2
_LAKE_POSITIONS: frozenset[tuple[int, int]] = frozenset(
    {
        (4, 2), (4, 3), (5, 2), (5, 3),
        (4, 6), (4, 7), (5, 6), (5, 7),
    }
)

BOARD_ROWS: int = 10
BOARD_COLS: int = 10

# Setup zone row ranges (inclusive).
_SETUP_ZONES: dict[PlayerSide, tuple[int, int]] = {
    PlayerSide.RED: (6, 9),
    PlayerSide.BLUE: (0, 3),
}


@dataclass(frozen=True)
class Square:
    """A single cell on the board."""

    position: Position
    terrain: TerrainType
    piece: Piece | None = field(default=None)


@dataclass(frozen=True)
class Board:
    """Immutable 10×10 board representation.

    The board is the authoritative source for piece positions.
    """

    squares: dict[tuple[int, int], Square]

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def create_empty(cls) -> Board:
        """Return a fresh board with all lake squares pre-populated and no pieces."""
        squares: dict[tuple[int, int], Square] = {}
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                terrain = (
                    TerrainType.LAKE
                    if (row, col) in _LAKE_POSITIONS
                    else TerrainType.NORMAL
                )
                squares[(row, col)] = Square(
                    position=Position(row, col),
                    terrain=terrain,
                    piece=None,
                )
        return cls(squares=squares)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_square(self, pos: Position) -> Square:
        """Return the square at *pos*. Raises KeyError for invalid positions."""
        return self.squares[(pos.row, pos.col)]

    def is_lake(self, pos: Position) -> bool:
        """Return True iff *pos* is a lake square."""
        return self.squares.get((pos.row, pos.col), None) is not None and (
            self.squares[(pos.row, pos.col)].terrain == TerrainType.LAKE
        )

    def is_empty(self, pos: Position) -> bool:
        """Return True iff *pos* contains no piece (and is not a lake)."""
        sq = self.squares.get((pos.row, pos.col))
        return sq is not None and sq.terrain != TerrainType.LAKE and sq.piece is None

    def neighbours(self, pos: Position) -> list[Position]:
        """Return all valid orthogonal neighbours of *pos* (excludes diagonals)."""
        candidates = [
            Position(pos.row - 1, pos.col),
            Position(pos.row + 1, pos.col),
            Position(pos.row, pos.col - 1),
            Position(pos.row, pos.col + 1),
        ]
        return [p for p in candidates if p.is_valid()]

    def is_in_setup_zone(self, pos: Position, side: PlayerSide) -> bool:
        """Return True iff *pos* is in *side*'s setup zone (rows 6–9 for RED, 0–3 for BLUE)."""
        low, high = _SETUP_ZONES[side]
        return low <= pos.row <= high

    def place_piece(self, piece: Piece) -> Board:
        """Return a new Board with *piece* placed at *piece.position*.

        Raises ValueError if the target square is a lake or already occupied.
        """
        pos = piece.position
        sq = self.squares.get((pos.row, pos.col))
        if sq is None:
            raise ValueError(f"Position {pos} is outside the board.")
        if sq.terrain == TerrainType.LAKE:
            raise ValueError(f"Cannot place piece on lake square {pos}.")
        if sq.piece is not None:
            raise ValueError(f"Square {pos} is already occupied.")
        new_square = Square(position=sq.position, terrain=sq.terrain, piece=piece)
        new_squares = dict(self.squares)
        new_squares[(pos.row, pos.col)] = new_square
        return Board(squares=new_squares)

    def remove_piece(self, pos: Position) -> Board:
        """Return a new Board with the piece at *pos* removed."""
        sq = self.squares.get((pos.row, pos.col))
        if sq is None:
            raise ValueError(f"Position {pos} is outside the board.")
        new_square = Square(position=sq.position, terrain=sq.terrain, piece=None)
        new_squares = dict(self.squares)
        new_squares[(pos.row, pos.col)] = new_square
        return Board(squares=new_squares)

    def move_piece(self, from_pos: Position, to_pos: Position) -> Board:
        """Return a new Board with the piece moved from *from_pos* to *to_pos*.

        Raises ValueError if *from_pos* has no piece, or if *to_pos* is outside
        the board. The caller is responsible for validating legality before calling
        this method.
        """
        from_sq = self.squares.get((from_pos.row, from_pos.col))
        if from_sq is None:
            raise ValueError(f"Position {from_pos} is outside the board.")
        if from_sq.piece is None:
            raise ValueError(f"No piece at {from_pos} to move.")
        to_sq = self.squares.get((to_pos.row, to_pos.col))
        if to_sq is None:
            raise ValueError(f"Position {to_pos} is outside the board.")

        from dataclasses import replace as dc_replace

        moved_piece = dc_replace(from_sq.piece, position=to_pos, has_moved=True)
        new_squares = dict(self.squares)
        new_squares[(from_pos.row, from_pos.col)] = Square(
            position=from_sq.position, terrain=from_sq.terrain, piece=None
        )
        new_squares[(to_pos.row, to_pos.col)] = Square(
            position=to_sq.position, terrain=to_sq.terrain, piece=moved_piece
        )
        return Board(squares=new_squares)
