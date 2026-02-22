"""
src/domain/combat.py

Combat resolution between two Pieces.
Specification: game_components.md §5 (Combat Resolution)
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from src.domain.enums import CombatOutcome, Rank
from src.domain.piece import Piece


@dataclass(frozen=True)
class CombatResult:
    """Outcome of a single combat engagement.

    Both `attacker` and `defender` are the *post-combat* states of the
    pieces (with `revealed=True` applied, as required by game_components.md §5.3).
    """

    attacker: Piece
    defender: Piece
    outcome: CombatOutcome
    attacker_survived: bool
    defender_survived: bool


def resolve_combat(attacker: Piece, defender: Piece) -> CombatResult:
    """Resolve combat between *attacker* and *defender* and return the result.

    Special rules (game_components.md §5.2):
    - Miner (rank 3) defeats Bomb (rank 99).
    - Spy (rank 1) defeats Marshal (rank 10) **only when Spy is the attacker**.
    - Any piece defeats Flag — game ends (caller checks for Flag).
    - Bomb defeats all attackers except Miner.
    - Equal ranks → draw (both removed).
    - Otherwise: higher rank wins.

    Both pieces are marked `revealed=True` in the returned CombatResult
    regardless of the outcome (game_components.md §5.3).
    """
    # Mark both pieces as revealed (post-combat state).
    revealed_attacker = replace(attacker, revealed=True)
    revealed_defender = replace(defender, revealed=True)

    outcome = _determine_outcome(attacker.rank, defender.rank)

    attacker_survived = outcome == CombatOutcome.ATTACKER_WINS
    defender_survived = outcome == CombatOutcome.DEFENDER_WINS

    return CombatResult(
        attacker=revealed_attacker,
        defender=revealed_defender,
        outcome=outcome,
        attacker_survived=attacker_survived,
        defender_survived=defender_survived,
    )


def _determine_outcome(attacker_rank: Rank, defender_rank: Rank) -> CombatOutcome:
    """Pure function: map (attacker_rank, defender_rank) → CombatOutcome."""

    # Flag is always captured — attacker wins unconditionally.
    if defender_rank == Rank.FLAG:
        return CombatOutcome.ATTACKER_WINS

    # Bomb rules: only Miner survives.
    if defender_rank == Rank.BOMB:
        if attacker_rank == Rank.MINER:
            return CombatOutcome.ATTACKER_WINS
        return CombatOutcome.DEFENDER_WINS

    # Spy vs Marshal (special: Spy initiates only).
    if attacker_rank == Rank.SPY and defender_rank == Rank.MARSHAL:
        return CombatOutcome.ATTACKER_WINS

    # Draw on equal rank.
    if attacker_rank == defender_rank:
        return CombatOutcome.DRAW

    # Standard: higher integer rank wins.
    if attacker_rank > defender_rank:
        return CombatOutcome.ATTACKER_WINS
    return CombatOutcome.DEFENDER_WINS
