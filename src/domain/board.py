"""Board value object for the 10×10 Stratego playing field."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.enums import PlayerSide, TerrainType
from src.domain.piece import Piece
from src.domain.position import Position
from src.domain.square import Square

# The eight lake squares that cannot be entered by any piece.
LAKE_POSITIONS: frozenset[Position] = frozenset(
    {
        Position(4, 2),
        Position(4, 3),
        Position(5, 2),
        Position(5, 3),
        Position(4, 6),
        Position(4, 7),
        Position(5, 6),
        Position(5, 7),
    }
)

_BOARD_SIZE: int = 10

# Setup zone row ranges (inclusive) per side.
_RED_SETUP_ROWS: tuple[int, int] = (6, 9)
_BLUE_SETUP_ROWS: tuple[int, int] = (0, 3)


@dataclass(frozen=True)
class Board:
    """Immutable 10×10 Stratego board.

    The ``squares`` dict maps every valid ``Position`` to its ``Square``.
    The dict itself is not frozen by Python, but all public mutation methods
    return a *new* ``Board`` instance; callers must never mutate ``squares``
    directly.
    """

    squares: dict[Position, Square] = field(default_factory=dict)

    @classmethod
    def create_empty(cls) -> Board:
        """Return a fresh board with no pieces and correct lake terrain."""
        squares: dict[Position, Square] = {}
        for row in range(_BOARD_SIZE):
            for col in range(_BOARD_SIZE):
                pos = Position(row, col)
                terrain = TerrainType.LAKE if pos in LAKE_POSITIONS else TerrainType.NORMAL
                squares[pos] = Square(position=pos, piece=None, terrain=terrain)
        return cls(squares=squares)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def is_lake(self, pos: Position) -> bool:
        """Return True when *pos* is a lake square."""
        return pos in LAKE_POSITIONS

    def get_square(self, pos: Position) -> Square:
        """Return the ``Square`` at *pos*."""
        return self.squares[pos]

    def neighbours(self, pos: Position) -> list[Position]:
        """Return all orthogonally adjacent positions that are within bounds."""
        candidates = [
            Position(pos.row - 1, pos.col),
            Position(pos.row + 1, pos.col),
            Position(pos.row, pos.col - 1),
            Position(pos.row, pos.col + 1),
        ]
        return [p for p in candidates if p.is_valid()]

    def is_empty(self, pos: Position) -> bool:
        """Return True when *pos* contains no piece."""
        return self.squares[pos].piece is None

    def is_in_setup_zone(self, pos: Position, side: PlayerSide) -> bool:
        """Return True when *pos* is inside *side*'s setup zone.

        RED occupies rows 6–9; BLUE occupies rows 0–3.
        """
        if side is PlayerSide.RED:
            return _RED_SETUP_ROWS[0] <= pos.row <= _RED_SETUP_ROWS[1]
        return _BLUE_SETUP_ROWS[0] <= pos.row <= _BLUE_SETUP_ROWS[1]

    # ------------------------------------------------------------------
    # Immutable "mutation" helpers – each returns a new Board
    # ------------------------------------------------------------------

    def place_piece(self, piece: Piece, pos: Position) -> Board:
        """Return a new board with *piece* placed at *pos*."""
        new_squares = dict(self.squares)
        existing = new_squares[pos]
        new_squares[pos] = Square(position=pos, piece=piece, terrain=existing.terrain)
        return Board(squares=new_squares)

    def remove_piece(self, pos: Position) -> Board:
        """Return a new board with the piece at *pos* removed."""
        new_squares = dict(self.squares)
        existing = new_squares[pos]
        new_squares[pos] = Square(position=pos, piece=None, terrain=existing.terrain)
        return Board(squares=new_squares)

    def move_piece(self, from_pos: Position, to_pos: Position) -> Board:
        """Return a new board with the piece moved from *from_pos* to *to_pos*.

        Any piece previously occupying *to_pos* is replaced.  The piece's
        ``has_moved`` flag is set to ``True``.
        """
        piece = self.squares[from_pos].piece
        if piece is None:
            raise ValueError(f"No piece at {from_pos}")
        moved_piece = Piece(
            rank=piece.rank,
            owner=piece.owner,
            revealed=piece.revealed,
            has_moved=True,
            position=to_pos,
        )
        new_squares = dict(self.squares)
        src_square = new_squares[from_pos]
        dst_square = new_squares[to_pos]
        new_squares[from_pos] = Square(
            position=from_pos, piece=None, terrain=src_square.terrain
        )
        new_squares[to_pos] = Square(
            position=to_pos, piece=moved_piece, terrain=dst_square.terrain
        )
        return Board(squares=new_squares)
