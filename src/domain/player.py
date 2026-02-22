"""Player value object representing one side's state in the game."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.enums import PlayerSide, PlayerType
from src.domain.piece import Piece
from src.domain.position import Position


@dataclass(frozen=True)
class Player:
    """Immutable snapshot of one player's in-game state."""

    side: PlayerSide
    player_type: PlayerType
    pieces_remaining: tuple[Piece, ...]
    flag_position: Position | None
