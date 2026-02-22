"""Combat resolution logic for Stratego piece engagements."""

from src.domain.combat_result import CombatResult
from src.domain.enums import CombatOutcome, Rank
from src.domain.piece import Piece


def resolve_combat(attacker: Piece, defender: Piece) -> CombatResult:
    """Determine the outcome when *attacker* moves onto *defender*'s square.

    Special rules (in priority order):
    1. Defender is FLAG → attacker always wins (triggers game over for caller).
    2. Defender is BOMB → only a MINER can defuse it; all others lose.
    3. Attacker is SPY *and* defender is MARSHAL → attacker wins (spy ability).
    4. General case: higher rank wins; equal ranks → DRAW (both removed).

    Both pieces in the returned ``CombatResult`` have ``revealed=True``.
    """
    revealed_attacker = Piece(
        rank=attacker.rank,
        owner=attacker.owner,
        revealed=True,
        has_moved=attacker.has_moved,
        position=attacker.position,
    )
    revealed_defender = Piece(
        rank=defender.rank,
        owner=defender.owner,
        revealed=True,
        has_moved=defender.has_moved,
        position=defender.position,
    )

    outcome, attacker_survived, defender_survived = _compute_outcome(attacker, defender)

    return CombatResult(
        attacker=revealed_attacker,
        defender=revealed_defender,
        outcome=outcome,
        attacker_survived=attacker_survived,
        defender_survived=defender_survived,
    )


def _compute_outcome(
    attacker: Piece, defender: Piece
) -> tuple[CombatOutcome, bool, bool]:
    """Return (outcome, attacker_survived, defender_survived) for the engagement."""
    # Rule 1: flag capture
    if defender.rank is Rank.FLAG:
        return CombatOutcome.ATTACKER_WINS, True, False

    # Rule 2: bomb – only miner defuses it
    if defender.rank is Rank.BOMB:
        if attacker.rank is Rank.MINER:
            return CombatOutcome.ATTACKER_WINS, True, False
        return CombatOutcome.DEFENDER_WINS, False, True

    # Rule 3: spy's special ability (only when spy *attacks* marshal)
    if attacker.rank is Rank.SPY and defender.rank is Rank.MARSHAL:
        return CombatOutcome.ATTACKER_WINS, True, False

    # Rule 4: general rank comparison
    if attacker.rank > defender.rank:
        return CombatOutcome.ATTACKER_WINS, True, False
    if attacker.rank < defender.rank:
        return CombatOutcome.DEFENDER_WINS, False, True
    # Equal ranks – draw
    return CombatOutcome.DRAW, False, False
