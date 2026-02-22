"""CombatResult value object capturing the outcome of a Stratego battle."""

from dataclasses import dataclass

from src.domain.enums import CombatOutcome
from src.domain.piece import Piece


@dataclass(frozen=True)
class CombatResult:
    """Immutable record of a combat engagement between two pieces."""

    attacker: Piece
    defender: Piece
    outcome: CombatOutcome
    attacker_survived: bool
    defender_survived: bool
