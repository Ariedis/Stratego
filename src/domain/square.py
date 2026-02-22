"""Square value object representing a single cell on the Stratego board."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.enums import TerrainType
from src.domain.piece import Piece
from src.domain.position import Position


@dataclass(frozen=True)
class Square:
    """An immutable board cell holding terrain type and an optional piece."""

    position: Position
    piece: Piece | None
    terrain: TerrainType
