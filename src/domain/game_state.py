"""GameState value object – the complete, immutable state of one game."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.board import Board
from src.domain.enums import GamePhase, PlayerSide
from src.domain.move_record import MoveRecord
from src.domain.player import Player


@dataclass(frozen=True)
class GameState:
    """Complete snapshot of the Stratego game at a single point in time."""

    board: Board
    players: tuple[Player, Player]
    active_player: PlayerSide
    phase: GamePhase
    turn_number: int
    move_history: tuple[MoveRecord, ...]
    winner: PlayerSide | None
