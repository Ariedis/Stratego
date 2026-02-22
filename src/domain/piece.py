"""
src/domain/piece.py

Immutable Piece value object.
Specification: data_models.md §3 (Piece entity)
"""
from __future__ import annotations

from dataclasses import dataclass

from src.domain.enums import PlayerSide, Rank


@dataclass(frozen=True)
class Position:
    """A board coordinate. Valid range: 0 ≤ row ≤ 9, 0 ≤ col ≤ 9."""

    row: int
    col: int

    def is_valid(self) -> bool:
        """Return True iff this position lies within the 10×10 board."""
        return 0 <= self.row <= 9 and 0 <= self.col <= 9


@dataclass(frozen=True)
class Piece:
    """An immutable snapshot of a single game piece.

    Invariants (from data_models.md §4):
    - A FLAG or BOMB piece must never have has_moved == True (I-4).
    - piece.position must always equal the Board square that contains it (I-9).
    """

    rank: Rank
    owner: PlayerSide
    revealed: bool
    has_moved: bool
    position: Position
