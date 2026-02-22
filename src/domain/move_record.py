"""MoveRecord value object capturing a completed turn in the game history."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.combat_result import CombatResult
from src.domain.move import Move


@dataclass(frozen=True)
class MoveRecord:
    """Immutable journal entry for one completed game turn."""

    move: Move
    combat_result: CombatResult | None
    turn_number: int
    timestamp: float
