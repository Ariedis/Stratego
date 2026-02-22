"""
src/domain/player.py

Player value object.
Specification: data_models.md §3 (Player entity)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.enums import PlayerSide, PlayerType
from src.domain.piece import Piece, Position


@dataclass(frozen=True)
class Player:
    """Immutable snapshot of one player's state."""

    side: PlayerSide
    player_type: PlayerType
    pieces_remaining: tuple[Piece, ...] = field(default_factory=tuple)
    flag_position: Position | None = None
