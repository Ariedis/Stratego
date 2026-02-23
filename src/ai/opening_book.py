"""
src/ai/opening_book.py

Opening book for the Stratego AI — predefined piece setups for each difficulty.
Specification: ai_strategy.md §4.1
"""
from __future__ import annotations

import random

from src.domain.enums import PlayerSide, PlayerType, Rank
from src.domain.piece import Piece, Position

# ---------------------------------------------------------------------------
# Stratego piece counts (total 40 pieces per side)
# ---------------------------------------------------------------------------
#   Marshal: 1, General: 1, Colonel: 2, Major: 3, Captain: 4, Lieutenant: 4,
#   Sergeant: 4, Miner: 5, Scout: 8, Spy: 1, Bomb: 6, Flag: 1

# ---------------------------------------------------------------------------
# Fortress base setup for RED (rows 6–9)
#
# Layout (row, col) → Rank:
#   Row 9 (back): FLAG at (9,0), 2 BOMBs at (9,1)/(9,2), 6 SCOUTs at cols 3–9 wait...
# Counts: Flag=1, Bomb=6, Scout=8, Miner=5, Marshal=1, General=1, Colonel=2,
#         Major=3, Captain=4, Lieutenant=4, Sergeant=4, Spy=1  → 40
#
# Fortress positions (Flag deep in corner, ≥3 adjacent Bombs):
#   Row 9: FLAG(9,0), BOMB(9,1), BOMB(9,2), SCOUT×6: (9,3)–(9,8), SCOUT(9,9)  → 1+2+7 = 10
#          wait: 1FLAG + 2BOMB + 7SCOUT = 10 but we only have 8 scouts total.
#
# Let's plan carefully:
#   Row 9: FLAG, BOMB, BOMB, BOMB, SCOUT, SCOUT, SCOUT, SCOUT, SCOUT, SCOUT  = 1+3+6=10
#   Row 8: BOMB, BOMB, BOMB, MINER, MINER, MINER, MINER, MINER, SCOUT, SCOUT = 3+5+2=10
#   Row 7: MARSHAL, GENERAL, COLONEL, COLONEL, MAJOR, MAJOR, MAJOR,
#          CAPTAIN, SERGEANT, SERGEANT                                         = 10
#   Row 6: CAPTAIN, CAPTAIN, CAPTAIN, LIEUTENANT, LIEUTENANT, LIEUTENANT,
#          LIEUTENANT, SERGEANT, SERGEANT, SPY                                 = 10
#
# Bombs: 3 (row9) + 3 (row8) = 6 ✓
# Scouts: 6 (row9) + 2 (row8) = 8 ✓
# Miners: 5 (row8) ✓
# FLAG adjacent bombs check: FLAG at (9,0), adjacent = (8,0)=BOMB, (8,1)=BOMB, (9,1)=BOMB → 3 ✓
# ---------------------------------------------------------------------------

_FORTRESS_RED: list[tuple[int, int, Rank]] = [
    # Row 9 (back row)
    (9, 0, Rank.FLAG),
    (9, 1, Rank.BOMB),
    (9, 2, Rank.BOMB),
    (9, 3, Rank.BOMB),
    (9, 4, Rank.SCOUT),
    (9, 5, Rank.SCOUT),
    (9, 6, Rank.SCOUT),
    (9, 7, Rank.SCOUT),
    (9, 8, Rank.SCOUT),
    (9, 9, Rank.SCOUT),
    # Row 8
    (8, 0, Rank.BOMB),
    (8, 1, Rank.BOMB),
    (8, 2, Rank.BOMB),
    (8, 3, Rank.MINER),
    (8, 4, Rank.MINER),
    (8, 5, Rank.MINER),
    (8, 6, Rank.MINER),
    (8, 7, Rank.MINER),
    (8, 8, Rank.SCOUT),
    (8, 9, Rank.SCOUT),
    # Row 7
    (7, 0, Rank.MARSHAL),
    (7, 1, Rank.GENERAL),
    (7, 2, Rank.COLONEL),
    (7, 3, Rank.COLONEL),
    (7, 4, Rank.MAJOR),
    (7, 5, Rank.MAJOR),
    (7, 6, Rank.MAJOR),
    (7, 7, Rank.CAPTAIN),
    (7, 8, Rank.SERGEANT),
    (7, 9, Rank.SERGEANT),
    # Row 6
    (6, 0, Rank.CAPTAIN),
    (6, 1, Rank.CAPTAIN),
    (6, 2, Rank.CAPTAIN),
    (6, 3, Rank.LIEUTENANT),
    (6, 4, Rank.LIEUTENANT),
    (6, 5, Rank.LIEUTENANT),
    (6, 6, Rank.LIEUTENANT),
    (6, 7, Rank.SERGEANT),
    (6, 8, Rank.SERGEANT),
    (6, 9, Rank.SPY),
]

# ---------------------------------------------------------------------------
# Blitz base setup for RED (rows 6–9)
#
# Scouts and high-rank pieces in row 6; Marshal at (6,5); Flag deeper at (9,4).
# ---------------------------------------------------------------------------

_BLITZ_RED: list[tuple[int, int, Rank]] = [
    # Row 9 (back row)
    (9, 0, Rank.BOMB),
    (9, 1, Rank.BOMB),
    (9, 2, Rank.BOMB),
    (9, 3, Rank.BOMB),
    (9, 4, Rank.FLAG),
    (9, 5, Rank.BOMB),
    (9, 6, Rank.BOMB),
    (9, 7, Rank.SERGEANT),
    (9, 8, Rank.SERGEANT),
    (9, 9, Rank.SERGEANT),
    # Row 8
    (8, 0, Rank.MINER),
    (8, 1, Rank.MINER),
    (8, 2, Rank.MINER),
    (8, 3, Rank.MINER),
    (8, 4, Rank.MINER),
    (8, 5, Rank.LIEUTENANT),
    (8, 6, Rank.LIEUTENANT),
    (8, 7, Rank.LIEUTENANT),
    (8, 8, Rank.LIEUTENANT),
    (8, 9, Rank.SERGEANT),
    # Row 7
    (7, 0, Rank.COLONEL),
    (7, 1, Rank.COLONEL),
    (7, 2, Rank.MAJOR),
    (7, 3, Rank.MAJOR),
    (7, 4, Rank.MAJOR),
    (7, 5, Rank.CAPTAIN),
    (7, 6, Rank.CAPTAIN),
    (7, 7, Rank.CAPTAIN),
    (7, 8, Rank.CAPTAIN),
    (7, 9, Rank.GENERAL),
    # Row 6 (front row — aggressive)
    (6, 0, Rank.SCOUT),
    (6, 1, Rank.SCOUT),
    (6, 2, Rank.SCOUT),
    (6, 3, Rank.SCOUT),
    (6, 4, Rank.SCOUT),
    (6, 5, Rank.MARSHAL),
    (6, 6, Rank.SCOUT),
    (6, 7, Rank.SCOUT),
    (6, 8, Rank.SCOUT),
    (6, 9, Rank.SPY),
]

_STRATEGY_MAP: dict[str, list[tuple[int, int, Rank]]] = {
    "fortress": _FORTRESS_RED,
    "blitz": _BLITZ_RED,
}

# Lake positions — must be avoided (rows 4–5, cols 2–3 and 6–7).
_LAKE_CELLS: frozenset[tuple[int, int]] = frozenset(
    {(4, 2), (4, 3), (5, 2), (5, 3), (4, 6), (4, 7), (5, 6), (5, 7)}
)

# All valid positions in the RED setup zone (rows 6–9).
_RED_ZONE: list[tuple[int, int]] = [
    (r, c)
    for r in range(6, 10)
    for c in range(0, 10)
    if (r, c) not in _LAKE_CELLS
]

# All valid positions in the BLUE setup zone (rows 0–3).
_BLUE_ZONE: list[tuple[int, int]] = [
    (r, c)
    for r in range(0, 4)
    for c in range(0, 10)
    if (r, c) not in _LAKE_CELLS
]


def _mirror_row(row: int) -> int:
    """Mirror a RED-zone row to the corresponding BLUE-zone row (9-row)."""
    return 9 - row


def _build_setup(
    positions: list[tuple[int, int, Rank]],
    side: PlayerSide,
) -> dict[Position, Piece]:
    """Build a setup dictionary from a list of (row, col, rank) triples."""
    result: dict[Position, Piece] = {}
    for row, col, rank in positions:
        if side == PlayerSide.BLUE:
            row = _mirror_row(row)
        pos = Position(row, col)
        result[pos] = Piece(
            rank=rank,
            owner=side,
            revealed=False,
            has_moved=False,
            position=pos,
        )
    return result


def _shuffle_setup(
    positions: list[tuple[int, int, Rank]],
    side: PlayerSide,
) -> dict[Position, Piece]:
    """Randomly permute all piece positions within the setup zone."""
    zone = _RED_ZONE if side == PlayerSide.RED else _BLUE_ZONE
    ranks = [rank for _, _, rank in positions]
    sampled_positions = random.sample(zone, len(ranks))
    result: dict[Position, Piece] = {}
    for (row, col), rank in zip(sampled_positions, ranks):
        pos = Position(row, col)
        result[pos] = Piece(
            rank=rank,
            owner=side,
            revealed=False,
            has_moved=False,
            position=pos,
        )
    return result


def _perturb_setup(
    positions: list[tuple[int, int, Rank]],
    side: PlayerSide,
    perturbation_rate: float = 0.30,
) -> dict[Position, Piece]:
    """Apply random perturbations to a base setup.

    About *perturbation_rate* of piece positions are swapped with each other,
    producing a slightly different arrangement while preserving overall structure.
    """
    setup = list(positions)  # (row, col, rank)
    n = len(setup)
    num_swaps = max(1, int(n * perturbation_rate))
    indices = random.sample(range(n), min(num_swaps * 2, n))
    # Swap pairs of positions.
    for i in range(0, len(indices) - 1, 2):
        a, b = indices[i], indices[i + 1]
        ra, ca, rank_a = setup[a]
        rb, cb, rank_b = setup[b]
        setup[a] = (ra, ca, rank_b)
        setup[b] = (rb, cb, rank_a)
    return _build_setup(setup, side)


class OpeningBook:
    """Provides predefined initial piece arrangements for the AI player.

    Difficulty levels control the amount of randomisation applied:
    - HARD: deterministic base setup (Fortress or Blitz).
    - MEDIUM: 30 % random perturbation of the base setup.
    - EASY: fully random placement within the setup zone.

    Specification: ai_strategy.md §4.1.
    """

    def get_setup(
        self,
        difficulty: PlayerType,
        strategy: str = "fortress",
        side: PlayerSide = PlayerSide.RED,
    ) -> dict[Position, Piece]:
        """Return a 40-piece initial arrangement for *side* at *difficulty*.

        Parameters
        ----------
        difficulty:
            AI difficulty level; controls randomisation.
        strategy:
            Base layout to use ("fortress" or "blitz").  Ignored for EASY
            (fully random).
        side:
            Which side the pieces belong to.  BLUE positions are mirrored
            vertically so they occupy rows 0–3.

        Returns
        -------
        dict[Position, Piece]
            Exactly 40 pieces in valid, non-overlapping positions.
        """
        base = _STRATEGY_MAP.get(strategy, _FORTRESS_RED)

        if difficulty == PlayerType.AI_HARD:
            return _build_setup(base, side)
        if difficulty == PlayerType.AI_MEDIUM:
            return _perturb_setup(base, side, perturbation_rate=0.30)
        # AI_EASY: fully random.
        return _shuffle_setup(base, side)
