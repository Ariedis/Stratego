"""
test_probability_tracker.py — Unit tests for src/ai/probability_tracker.py

Epic: EPIC-5 | User Story: US-505
Covers acceptance criteria:
  AC-1: Initial uniform distribution over all 12 ranks, summing to 1.0
  AC-2: update_on_move() sets BOMB and FLAG probabilities to 0; renormalises
  AC-3: update_on_reveal() collapses distribution to {actual_rank: 1.0}
        and removes that rank from all other pieces' distributions
  AC-4: After any update, sum(distribution.values()) == 1.0 (± 1e-9)
Specification: ai_strategy.md §5
"""
from __future__ import annotations

import pytest

try:
    from src.ai.probability_tracker import ProbabilityTracker
    _TRACKER_AVAILABLE = True
except ImportError:
    _TRACKER_AVAILABLE = False
    ProbabilityTracker = None  # type: ignore[assignment]

from src.domain.enums import PlayerSide, Rank
from src.domain.piece import Piece, Position

pytestmark = pytest.mark.xfail(
    not _TRACKER_AVAILABLE,
    reason="src/ai/probability_tracker.py not yet implemented",
    strict=False,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TOLERANCE = 1e-9
_ALL_RANKS = list(Rank)
_MOVEABLE_RANKS = [r for r in Rank if r not in (Rank.BOMB, Rank.FLAG)]

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def _make_piece(rank: Rank, row: int, col: int, *, revealed: bool = False) -> Piece:
    return Piece(
        rank=rank,
        owner=PlayerSide.BLUE,
        revealed=revealed,
        has_moved=False,
        position=Position(row, col),
    )


@pytest.fixture
def three_blue_pieces() -> list[Piece]:
    """Three unrevealed BLUE pieces at distinct positions."""
    return [
        _make_piece(Rank.SCOUT, 1, 0),    # will be used for move update
        _make_piece(Rank.MINER, 1, 1),    # will be revealed as MINER
        _make_piece(Rank.CAPTAIN, 1, 2),  # will survive combat
    ]


@pytest.fixture
def tracker_three(three_blue_pieces: list[Piece]) -> ProbabilityTracker:
    """ProbabilityTracker initialised with three unrevealed BLUE pieces."""
    return ProbabilityTracker(opponent_pieces=three_blue_pieces)


@pytest.fixture
def single_piece() -> Piece:
    return _make_piece(Rank.SERGEANT, 2, 0)


@pytest.fixture
def tracker_single(single_piece: Piece) -> ProbabilityTracker:
    """ProbabilityTracker with a single piece."""
    return ProbabilityTracker(opponent_pieces=[single_piece])


# ---------------------------------------------------------------------------
# US-505 AC-1: Uniform initial distribution
# ---------------------------------------------------------------------------


class TestInitialDistribution:
    """AC-1: At start, every rank is equally probable for each unrevealed piece."""

    def test_initial_distribution_sums_to_one(
        self, tracker_single: ProbabilityTracker, single_piece: Piece
    ) -> None:
        """AC-1: Initial distribution sums to 1.0."""
        dist = tracker_single.get_distribution(single_piece)
        assert abs(sum(dist.values()) - 1.0) < _TOLERANCE

    def test_initial_distribution_is_uniform(
        self, tracker_single: ProbabilityTracker, single_piece: Piece
    ) -> None:
        """AC-1: Each rank has equal probability in the initial distribution."""
        dist = tracker_single.get_distribution(single_piece)
        values = list(dist.values())
        # All probabilities should be equal (uniform)
        assert max(values) - min(values) < _TOLERANCE, (
            "Initial distribution is not uniform."
        )

    def test_initial_distribution_covers_all_ranks(
        self, tracker_single: ProbabilityTracker, single_piece: Piece
    ) -> None:
        """AC-1: Initial distribution includes all 12 ranks."""
        dist = tracker_single.get_distribution(single_piece)
        assert set(dist.keys()) == set(Rank)

    def test_initial_distribution_all_probabilities_positive(
        self, tracker_single: ProbabilityTracker, single_piece: Piece
    ) -> None:
        """AC-1: Every rank starts with positive (> 0) probability."""
        dist = tracker_single.get_distribution(single_piece)
        for rank, prob in dist.items():
            assert prob > 0.0, f"Rank {rank.name} has zero initial probability."

    def test_initial_distribution_uniform_across_multiple_pieces(
        self, tracker_three: ProbabilityTracker, three_blue_pieces: list[Piece]
    ) -> None:
        """AC-1: All pieces in the tracker start with uniform distributions."""
        for piece in three_blue_pieces:
            dist = tracker_three.get_distribution(piece)
            assert abs(sum(dist.values()) - 1.0) < _TOLERANCE


# ---------------------------------------------------------------------------
# US-505 AC-2: update_on_move() eliminates BOMB and FLAG
# ---------------------------------------------------------------------------


class TestUpdateOnMove:
    """AC-2: Moving a piece eliminates BOMB and FLAG from its distribution."""

    def test_update_on_move_sets_bomb_probability_to_zero(
        self, tracker_single: ProbabilityTracker, single_piece: Piece
    ) -> None:
        """AC-2: After move update, BOMB probability is exactly 0."""
        tracker_single.update_on_move(single_piece)
        dist = tracker_single.get_distribution(single_piece)
        assert dist[Rank.BOMB] == 0.0

    def test_update_on_move_sets_flag_probability_to_zero(
        self, tracker_single: ProbabilityTracker, single_piece: Piece
    ) -> None:
        """AC-2: After move update, FLAG probability is exactly 0."""
        tracker_single.update_on_move(single_piece)
        dist = tracker_single.get_distribution(single_piece)
        assert dist[Rank.FLAG] == 0.0

    def test_update_on_move_renormalises_distribution(
        self, tracker_single: ProbabilityTracker, single_piece: Piece
    ) -> None:
        """AC-2: Distribution sums to 1.0 after update_on_move."""
        tracker_single.update_on_move(single_piece)
        dist = tracker_single.get_distribution(single_piece)
        assert abs(sum(dist.values()) - 1.0) < _TOLERANCE

    def test_update_on_move_preserves_equal_distribution_for_moveable_ranks(
        self, tracker_single: ProbabilityTracker, single_piece: Piece
    ) -> None:
        """AC-2: Remaining moveable ranks are equally probable after update."""
        tracker_single.update_on_move(single_piece)
        dist = tracker_single.get_distribution(single_piece)
        moveable_probs = [dist[r] for r in Rank if r not in (Rank.BOMB, Rank.FLAG)]
        # All moveable ranks should have equal probability
        assert max(moveable_probs) - min(moveable_probs) < _TOLERANCE

    def test_update_on_move_spec_example(
        self, tracker_three: ProbabilityTracker, three_blue_pieces: list[Piece]
    ) -> None:
        """Verbatim test from ai_strategy.md §5 example (US-505)."""
        piece = three_blue_pieces[0]
        tracker_three.update_on_move(piece)
        dist = tracker_three.get_distribution(piece)
        assert dist[Rank.BOMB] == 0.0
        assert dist[Rank.FLAG] == 0.0
        assert abs(sum(dist.values()) - 1.0) < _TOLERANCE

    def test_update_on_move_does_not_affect_other_pieces(
        self, tracker_three: ProbabilityTracker, three_blue_pieces: list[Piece]
    ) -> None:
        """AC-2: Updating one piece's distribution does not change others' BOMB/FLAG prob."""
        moved_piece = three_blue_pieces[0]
        other_piece = three_blue_pieces[1]

        dist_other_before = dict(tracker_three.get_distribution(other_piece))
        tracker_three.update_on_move(moved_piece)
        dist_other_after = tracker_three.get_distribution(other_piece)

        # The other piece's BOMB probability must remain unchanged
        assert abs(dist_other_after[Rank.BOMB] - dist_other_before[Rank.BOMB]) < _TOLERANCE


# ---------------------------------------------------------------------------
# US-505 AC-3: update_on_reveal() collapses distribution
# ---------------------------------------------------------------------------


class TestUpdateOnReveal:
    """AC-3: Revealing a piece collapses its distribution; propagates to others."""

    def test_reveal_collapses_distribution_to_one_rank(
        self, tracker_three: ProbabilityTracker, three_blue_pieces: list[Piece]
    ) -> None:
        """AC-3: After reveal, only the actual rank has probability 1.0."""
        piece = three_blue_pieces[1]
        tracker_three.update_on_reveal(piece, Rank.MINER)
        dist = tracker_three.get_distribution(piece)
        assert dist[Rank.MINER] == 1.0

    def test_reveal_sets_all_other_ranks_to_zero(
        self, tracker_three: ProbabilityTracker, three_blue_pieces: list[Piece]
    ) -> None:
        """AC-3: All ranks except the revealed rank have probability 0 after reveal."""
        piece = three_blue_pieces[1]
        tracker_three.update_on_reveal(piece, Rank.MINER)
        dist = tracker_three.get_distribution(piece)
        for rank, prob in dist.items():
            if rank != Rank.MINER:
                assert prob == 0.0, f"Rank {rank.name} should be 0 after MINER reveal."

    def test_reveal_removes_rank_from_other_pieces_distributions(
        self, tracker_three: ProbabilityTracker, three_blue_pieces: list[Piece]
    ) -> None:
        """AC-3: Revealed rank is eliminated from all other unrevealed pieces."""
        piece_revealed = three_blue_pieces[1]
        other_piece = three_blue_pieces[0]

        tracker_three.update_on_reveal(piece_revealed, Rank.MINER)
        dist_other = tracker_three.get_distribution(other_piece)
        assert dist_other[Rank.MINER] == 0.0, (
            "Revealed rank MINER should have probability 0 in other pieces' distributions."
        )

    def test_reveal_other_pieces_renormalised(
        self, tracker_three: ProbabilityTracker, three_blue_pieces: list[Piece]
    ) -> None:
        """AC-4 / AC-3: After reveal, other pieces' distributions still sum to 1.0."""
        piece_revealed = three_blue_pieces[1]
        tracker_three.update_on_reveal(piece_revealed, Rank.MINER)
        for piece in three_blue_pieces:
            dist = tracker_three.get_distribution(piece)
            assert abs(sum(dist.values()) - 1.0) < _TOLERANCE

    def test_reveal_scout_via_combat(
        self, tracker_three: ProbabilityTracker, three_blue_pieces: list[Piece]
    ) -> None:
        """AC-3: Verbatim US-505 example – reveal as SCOUT collapses to {SCOUT: 1.0}."""
        piece = three_blue_pieces[0]
        tracker_three.update_on_reveal(piece, Rank.SCOUT)
        dist = tracker_three.get_distribution(piece)
        assert dist[Rank.SCOUT] == 1.0
        for rank, prob in dist.items():
            if rank != Rank.SCOUT:
                assert prob == 0.0


# ---------------------------------------------------------------------------
# US-505 AC-4: Distribution normalisation invariant
# ---------------------------------------------------------------------------


class TestNormalisationInvariant:
    """AC-4: After any update, distribution must sum to 1.0 (± 1e-9)."""

    def test_distribution_sums_to_one_after_move_update(
        self, tracker_single: ProbabilityTracker, single_piece: Piece
    ) -> None:
        """AC-4: Normalisation holds after update_on_move."""
        tracker_single.update_on_move(single_piece)
        dist = tracker_single.get_distribution(single_piece)
        assert abs(sum(dist.values()) - 1.0) < _TOLERANCE

    def test_distribution_sums_to_one_after_reveal(
        self, tracker_three: ProbabilityTracker, three_blue_pieces: list[Piece]
    ) -> None:
        """AC-4: Normalisation holds after update_on_reveal for all pieces."""
        tracker_three.update_on_reveal(three_blue_pieces[0], Rank.SCOUT)
        for piece in three_blue_pieces:
            dist = tracker_three.get_distribution(piece)
            assert abs(sum(dist.values()) - 1.0) < _TOLERANCE

    def test_distribution_sums_to_one_after_combat_loss_update(
        self, tracker_three: ProbabilityTracker, three_blue_pieces: list[Piece]
    ) -> None:
        """AC-4: Normalisation holds after update_on_combat_loss."""
        piece = three_blue_pieces[2]
        # Piece survived combat with a SERGEANT (rank 4), so it must be rank > 4
        tracker_three.update_on_combat_loss(piece, Rank.SERGEANT)
        dist = tracker_three.get_distribution(piece)
        assert abs(sum(dist.values()) - 1.0) < _TOLERANCE

    def test_distribution_sums_to_one_after_multiple_updates(
        self, tracker_three: ProbabilityTracker, three_blue_pieces: list[Piece]
    ) -> None:
        """AC-4: Normalisation holds after a sequence of mixed updates."""
        tracker_three.update_on_move(three_blue_pieces[0])
        tracker_three.update_on_reveal(three_blue_pieces[1], Rank.MINER)
        tracker_three.update_on_combat_loss(three_blue_pieces[2], Rank.SERGEANT)
        for piece in three_blue_pieces:
            dist = tracker_three.get_distribution(piece)
            assert abs(sum(dist.values()) - 1.0) < _TOLERANCE


# ---------------------------------------------------------------------------
# update_on_combat_loss() — TASK-507 §5
# ---------------------------------------------------------------------------


class TestUpdateOnCombatLoss:
    """Surviving combat eliminates ranks ≤ loser's rank from the survivor's distribution."""

    def test_combat_loss_eliminates_lower_or_equal_ranks(
        self, tracker_three: ProbabilityTracker, three_blue_pieces: list[Piece]
    ) -> None:
        """Ranks ≤ SERGEANT (4) must be 0 after surviving combat with a SERGEANT."""
        piece = three_blue_pieces[2]
        tracker_three.update_on_combat_loss(piece, Rank.SERGEANT)
        dist = tracker_three.get_distribution(piece)
        for rank in Rank:
            if rank.value <= Rank.SERGEANT.value and rank != Rank.BOMB:
                assert dist.get(rank, 0.0) == 0.0, (
                    f"Rank {rank.name} (value {rank.value}) should be 0 after "
                    f"surviving SERGEANT combat."
                )

    def test_combat_loss_higher_ranks_still_possible(
        self, tracker_three: ProbabilityTracker, three_blue_pieces: list[Piece]
    ) -> None:
        """Ranks above the loser's rank remain possible after combat survival."""
        piece = three_blue_pieces[2]
        tracker_three.update_on_combat_loss(piece, Rank.SERGEANT)
        dist = tracker_three.get_distribution(piece)
        higher_rank_probs = [
            dist[r] for r in Rank
            if r.value > Rank.SERGEANT.value and r not in (Rank.BOMB, Rank.FLAG)
        ]
        assert any(p > 0.0 for p in higher_rank_probs), (
            "Some ranks above SERGEANT should remain possible."
        )


# ---------------------------------------------------------------------------
# get_most_likely_rank() — TASK-507 §7
# ---------------------------------------------------------------------------


class TestGetMostLikelyRank:
    """get_most_likely_rank() returns the rank with the highest probability."""

    def test_most_likely_rank_after_move_is_not_bomb_or_flag(
        self, tracker_single: ProbabilityTracker, single_piece: Piece
    ) -> None:
        """After a move, the most likely rank must be a moveable piece."""
        tracker_single.update_on_move(single_piece)
        most_likely = tracker_single.get_most_likely_rank(single_piece)
        assert most_likely not in (Rank.BOMB, Rank.FLAG)

    def test_most_likely_rank_after_reveal_is_revealed_rank(
        self, tracker_three: ProbabilityTracker, three_blue_pieces: list[Piece]
    ) -> None:
        """After reveal, most_likely_rank must equal the revealed rank."""
        piece = three_blue_pieces[0]
        tracker_three.update_on_reveal(piece, Rank.MARSHAL)
        most_likely = tracker_three.get_most_likely_rank(piece)
        assert most_likely == Rank.MARSHAL
