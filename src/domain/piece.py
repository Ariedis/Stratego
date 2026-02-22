"""Piece value object representing a single Stratego game piece."""

from dataclasses import dataclass

from src.domain.enums import PlayerSide, Rank
from src.domain.position import Position


@dataclass(frozen=True)
class Piece:
    """An immutable Stratego piece with rank, ownership and board state."""

    rank: Rank
    owner: PlayerSide
    revealed: bool
    has_moved: bool
    position: Position
