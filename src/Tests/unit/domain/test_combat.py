"""
test_combat.py — Unit tests for src/domain/combat.py

Epic: EPIC-2 | User Story: US-204
Covers acceptance criteria: AC-1 through AC-10
Specification: game_components.md §5 (Combat Resolution)
"""
from __future__ import annotations

import pytest

from src.domain.combat import resolve_combat
from src.domain.enums import CombatOutcome, PlayerSide, Rank
from src.domain.piece import Piece, Position


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def make_piece(rank: Rank, owner: PlayerSide = PlayerSide.RED) -> Piece:
    """Create a Piece at a stable test position."""
    return Piece(
        rank=rank,
        owner=owner,
        revealed=False,
        has_moved=False,
        position=Position(5, 5),
    )


# ---------------------------------------------------------------------------
# US-204 AC-1 through AC-3: Standard rank-based outcomes
# ---------------------------------------------------------------------------


class TestStandardCombatOutcomes:
    """Higher rank wins; equal rank draws (general principle)."""

    @pytest.mark.parametrize(
        "attacker_rank, defender_rank, expected_outcome",
        [
            # AC-1: Attacker rank > defender rank → attacker wins
            (Rank.SERGEANT, Rank.MINER, CombatOutcome.ATTACKER_WINS),
            # AC-2: Attacker rank < defender rank → defender wins
            (Rank.SPY, Rank.CAPTAIN, CombatOutcome.DEFENDER_WINS),
            # AC-3: Equal ranks → draw
            (Rank.COLONEL, Rank.COLONEL, CombatOutcome.DRAW),
            # Additional pairings
            (Rank.GENERAL, Rank.MAJOR, CombatOutcome.ATTACKER_WINS),
            (Rank.LIEUTENANT, Rank.MARSHAL, CombatOutcome.DEFENDER_WINS),
            (Rank.MINER, Rank.MINER, CombatOutcome.DRAW),
        ],
        ids=[
            "ac1_sergeant_beats_miner",
            "ac2_spy_loses_to_captain",
            "ac3_colonel_vs_colonel_draw",
            "general_beats_major",
            "lieutenant_loses_to_marshal",
            "miner_vs_miner_draw",
        ],
    )
    def test_rank_comparison_outcome(
        self,
        attacker_rank: Rank,
        defender_rank: Rank,
        expected_outcome: CombatOutcome,
    ) -> None:
        attacker = make_piece(attacker_rank, PlayerSide.RED)
        defender = make_piece(defender_rank, PlayerSide.BLUE)
        result = resolve_combat(attacker, defender)
        assert result.outcome == expected_outcome


# ---------------------------------------------------------------------------
# US-204 AC-4 & AC-5: Spy / Marshal special interaction
# ---------------------------------------------------------------------------


class TestSpyMarshalInteraction:
    """Spy's special ability only applies when Spy initiates the attack."""

    def test_spy_attacking_marshal_spy_wins(self) -> None:
        """AC-4: Spy attacks Marshal → Spy wins; Marshal removed."""
        spy = make_piece(Rank.SPY, PlayerSide.RED)
        marshal = make_piece(Rank.MARSHAL, PlayerSide.BLUE)
        result = resolve_combat(attacker=spy, defender=marshal)
        assert result.outcome == CombatOutcome.ATTACKER_WINS
        assert result.attacker_survived is True
        assert result.defender_survived is False

    def test_marshal_attacking_spy_marshal_wins(self) -> None:
        """AC-5: Marshal attacks Spy → Marshal wins (normal rank comparison)."""
        marshal = make_piece(Rank.MARSHAL, PlayerSide.RED)
        spy = make_piece(Rank.SPY, PlayerSide.BLUE)
        result = resolve_combat(attacker=marshal, defender=spy)
        assert result.outcome == CombatOutcome.ATTACKER_WINS
        assert result.attacker_survived is True
        assert result.defender_survived is False

    def test_spy_defending_against_marshal_spy_loses(self) -> None:
        """AC-10: Spy defends against Marshal → Spy loses (rule only on Spy's attack)."""
        marshal = make_piece(Rank.MARSHAL, PlayerSide.RED)
        spy = make_piece(Rank.SPY, PlayerSide.BLUE)
        result = resolve_combat(attacker=marshal, defender=spy)
        assert result.outcome == CombatOutcome.ATTACKER_WINS
        assert result.defender_survived is False

    def test_spy_attacking_non_marshal_spy_loses(self) -> None:
        """AC-2 variant: Spy attacking any non-Marshal piece loses (rank 1 is lowest moveable)."""
        spy = make_piece(Rank.SPY, PlayerSide.RED)
        captain = make_piece(Rank.CAPTAIN, PlayerSide.BLUE)
        result = resolve_combat(attacker=spy, defender=captain)
        assert result.outcome == CombatOutcome.DEFENDER_WINS


# ---------------------------------------------------------------------------
# US-204 AC-6 & AC-7: Bomb interactions
# ---------------------------------------------------------------------------


class TestBombInteractions:
    """Bombs defeat all attackers; Miners are the sole exception."""

    def test_miner_attacks_bomb_miner_wins(self) -> None:
        """AC-6: Miner attacks Bomb → Miner wins; Bomb removed."""
        miner = make_piece(Rank.MINER, PlayerSide.RED)
        bomb = make_piece(Rank.BOMB, PlayerSide.BLUE)
        result = resolve_combat(attacker=miner, defender=bomb)
        assert result.outcome == CombatOutcome.ATTACKER_WINS
        assert result.attacker_survived is True
        assert result.defender_survived is False

    @pytest.mark.parametrize(
        "attacker_rank",
        [
            Rank.SPY, Rank.SCOUT, Rank.SERGEANT, Rank.LIEUTENANT,
            Rank.CAPTAIN, Rank.MAJOR, Rank.COLONEL, Rank.GENERAL, Rank.MARSHAL,
        ],
        ids=lambda r: r.name,
    )
    def test_non_miner_attacks_bomb_loses(self, attacker_rank: Rank) -> None:
        """AC-7: Any piece except Miner loses when attacking a Bomb."""
        attacker = make_piece(attacker_rank, PlayerSide.RED)
        bomb = make_piece(Rank.BOMB, PlayerSide.BLUE)
        result = resolve_combat(attacker=attacker, defender=bomb)
        assert result.outcome == CombatOutcome.DEFENDER_WINS
        assert result.attacker_survived is False
        assert result.defender_survived is True


# ---------------------------------------------------------------------------
# US-204 AC-8: Flag capture
# ---------------------------------------------------------------------------


class TestFlagCapture:
    """Any piece that attacks the Flag wins, triggering game over."""

    @pytest.mark.parametrize(
        "attacker_rank",
        [r for r in Rank if r not in (Rank.FLAG, Rank.BOMB)],
        ids=lambda r: r.name,
    )
    def test_any_piece_captures_flag(self, attacker_rank: Rank) -> None:
        """AC-8: Any moveable piece attacking the Flag wins."""
        attacker = make_piece(attacker_rank, PlayerSide.RED)
        flag = make_piece(Rank.FLAG, PlayerSide.BLUE)
        result = resolve_combat(attacker=attacker, defender=flag)
        assert result.outcome == CombatOutcome.ATTACKER_WINS
        assert result.attacker_survived is True
        assert result.defender_survived is False


# ---------------------------------------------------------------------------
# US-204 AC-9: Post-combat revelation
# ---------------------------------------------------------------------------


class TestCombatRevelation:
    """After any combat, both pieces must have revealed=True."""

    def test_both_pieces_revealed_after_attacker_wins(self) -> None:
        """AC-9: Both pieces revealed after attacker wins."""
        attacker = make_piece(Rank.GENERAL, PlayerSide.RED)
        defender = make_piece(Rank.COLONEL, PlayerSide.BLUE)
        result = resolve_combat(attacker=attacker, defender=defender)
        assert result.attacker.revealed is True
        assert result.defender.revealed is True

    def test_both_pieces_revealed_after_defender_wins(self) -> None:
        """AC-9: Both pieces revealed after defender wins."""
        attacker = make_piece(Rank.SCOUT, PlayerSide.RED)
        defender = make_piece(Rank.MARSHAL, PlayerSide.BLUE)
        result = resolve_combat(attacker=attacker, defender=defender)
        assert result.outcome == CombatOutcome.DEFENDER_WINS
        assert result.attacker.revealed is True
        assert result.defender.revealed is True

    def test_both_pieces_revealed_after_draw(self) -> None:
        """AC-9 (draw): Both pieces revealed even when both are removed."""
        p1 = make_piece(Rank.MAJOR, PlayerSide.RED)
        p2 = make_piece(Rank.MAJOR, PlayerSide.BLUE)
        result = resolve_combat(attacker=p1, defender=p2)
        assert result.outcome == CombatOutcome.DRAW
        assert result.attacker.revealed is True
        assert result.defender.revealed is True

    def test_reveal_applies_even_if_already_revealed(self) -> None:
        """Revelation is idempotent — already-revealed pieces stay revealed."""
        revealed_attacker = Piece(
            rank=Rank.CAPTAIN,
            owner=PlayerSide.RED,
            revealed=True,
            has_moved=True,
            position=Position(5, 5),
        )
        defender = make_piece(Rank.LIEUTENANT, PlayerSide.BLUE)
        result = resolve_combat(attacker=revealed_attacker, defender=defender)
        assert result.attacker.revealed is True
        assert result.defender.revealed is True


# ---------------------------------------------------------------------------
# CombatResult structure tests
# ---------------------------------------------------------------------------


class TestCombatResultStructure:
    """CombatResult is an immutable value object with the correct fields."""

    def test_combat_result_is_immutable(self) -> None:
        attacker = make_piece(Rank.SERGEANT, PlayerSide.RED)
        defender = make_piece(Rank.MINER, PlayerSide.BLUE)
        result = resolve_combat(attacker, defender)
        with pytest.raises(Exception):
            result.outcome = CombatOutcome.DRAW  # type: ignore[misc]

    def test_draw_sets_both_survived_false(self) -> None:
        """In a draw, neither piece survives."""
        p1 = make_piece(Rank.SERGEANT, PlayerSide.RED)
        p2 = make_piece(Rank.SERGEANT, PlayerSide.BLUE)
        result = resolve_combat(p1, p2)
        assert result.outcome == CombatOutcome.DRAW
        assert result.attacker_survived is False
        assert result.defender_survived is False

    def test_user_story_example(self) -> None:
        """Verbatim example from US-204: Spy attacks Marshal → attacker wins."""
        spy = make_piece(Rank.SPY, PlayerSide.RED)
        marshal = make_piece(Rank.MARSHAL, PlayerSide.BLUE)
        result = resolve_combat(attacker=spy, defender=marshal)
        assert result.outcome == CombatOutcome.ATTACKER_WINS
        assert result.attacker_survived is True
        assert result.defender_survived is False
