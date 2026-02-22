"""
src/domain/move.py

Move and MoveRecord value objects.
Specification: data_models.md §3 (Move, MoveRecord entities)
"""
from __future__ import annotations

from dataclasses import dataclass

from src.domain.enums import MoveType
from src.domain.piece import Piece, Position


@dataclass(frozen=True)
class Move:
    """Represents a single intended piece movement before validation."""

    piece: Piece
    from_pos: Position
    to_pos: Position
    move_type: MoveType = MoveType.MOVE
