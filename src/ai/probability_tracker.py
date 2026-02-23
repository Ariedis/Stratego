"""
src/ai/probability_tracker.py

Bayesian probability tracker for opponent piece ranks.
Specification: ai_strategy.md §5
"""
from __future__ import annotations

from src.domain.enums import Rank
from src.domain.piece import Piece

_ALL_RANKS: frozenset[Rank] = frozenset(Rank)


class ProbabilityTracker:
    """Maintains a probability distribution over possible ranks for each unrevealed piece.

    Initial state: uniform distribution over all 12 ranks for each piece.

    Updates are triggered by:
    - A piece moves → BOMB and FLAG eliminated (immovable ranks).
    - A piece is revealed in combat → distribution collapses to the actual rank,
      which is then removed from all other pieces' distributions.
    - A piece survives combat with a piece of known rank R → all ranks ≤ R eliminated.

    After every update the distribution is renormalised so probabilities sum to 1.0.

    Specification: ai_strategy.md §5.
    """

    def __init__(self, opponent_pieces: list[Piece]) -> None:
        """Initialise a uniform distribution over all ranks for each piece.

        Parameters
        ----------
        opponent_pieces:
            The list of unrevealed opponent pieces to track.
        """
        # For each piece, maintain the set of still-possible ranks.
        self._possible: dict[Piece, set[Rank]] = {}
        for piece in opponent_pieces:
            self._possible[piece] = set(_ALL_RANKS)

    # ------------------------------------------------------------------
    # Update methods
    # ------------------------------------------------------------------

    def update_on_move(self, piece: Piece) -> None:
        """Remove BOMB and FLAG from *piece*'s possible ranks; renormalise.

        A piece that moves cannot be a BOMB or FLAG (both are immovable).

        Specification: ai_strategy.md §5.
        """
        if piece not in self._possible:
            return
        self._possible[piece].discard(Rank.BOMB)
        self._possible[piece].discard(Rank.FLAG)

    def update_on_reveal(self, piece: Piece, actual_rank: Rank) -> None:
        """Collapse *piece*'s distribution to *actual_rank* and propagate.

        After a piece is revealed:
        1. Its own distribution collapses to {actual_rank: 1.0}.
        2. *actual_rank* is removed from all other tracked pieces' distributions
           and those distributions are renormalised.

        Specification: ai_strategy.md §5.
        """
        if piece in self._possible:
            self._possible[piece] = {actual_rank}

        # Propagate: other pieces can no longer be *actual_rank*.
        for other, possible in self._possible.items():
            if other != piece:
                possible.discard(actual_rank)

    def update_on_combat_loss(self, piece: Piece, loser_rank: Rank) -> None:
        """Eliminate ranks ≤ *loser_rank* from *piece*'s possible ranks; renormalise.

        If *piece* survived combat against a piece of rank *loser_rank*, it must
        outrank *loser_rank*.  All ranks whose value ≤ loser_rank.value are
        eliminated (BOMB, whose value is 99, is never eliminated by this rule for
        any normal loser rank).

        Specification: ai_strategy.md §5.
        """
        if piece not in self._possible:
            return
        to_remove = {r for r in self._possible[piece] if r.value <= loser_rank.value}
        self._possible[piece] -= to_remove

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def get_distribution(self, piece: Piece) -> dict[Rank, float]:
        """Return the current probability distribution for *piece*.

        The distribution is uniform over the current set of possible ranks and
        always sums to 1.0 (provided at least one rank is possible).

        Returns
        -------
        dict[Rank, float]
            Mapping of every Rank to its probability.  Impossible ranks have
            probability 0.0.  Probabilities sum to 1.0 (± floating-point noise).
        """
        possible = self._possible.get(piece, set())
        if not possible:
            return {r: 0.0 for r in Rank}
        prob = 1.0 / len(possible)
        return {r: (prob if r in possible else 0.0) for r in Rank}

    def get_most_likely_rank(self, piece: Piece) -> Rank:
        """Return the rank with the highest probability for *piece*.

        In a uniform distribution (most common case), ties are broken by the
        iteration order of the Rank enum.

        Specification: ai_strategy.md §5.
        """
        dist = self.get_distribution(piece)
        return max(dist, key=lambda r: dist[r])
