"""
src/application/commands.py

Command objects for the Stratego application layer.
Specification: system_design.md §2.2
"""
from __future__ import annotations

from dataclasses import dataclass

from src.domain.piece import Piece, Position


@dataclass(frozen=True)
class PlacePiece:
    """Command to place a piece during the setup phase."""

    piece: Piece
    pos: Position


@dataclass(frozen=True)
class MovePiece:
    """Command to move a piece during the playing phase."""

    from_pos: Position
    to_pos: Position


#: Union type alias for all supported commands.
Command = PlacePiece | MovePiece
