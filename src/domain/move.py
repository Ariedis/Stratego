"""Move value object describing a single piece movement or attack."""

from dataclasses import dataclass

from src.domain.enums import MoveType
from src.domain.piece import Piece
from src.domain.position import Position


@dataclass(frozen=True)
class Move:
    """An immutable description of one player action (move or attack)."""

    piece: Piece
    from_pos: Position
    to_pos: Position
    move_type: MoveType
