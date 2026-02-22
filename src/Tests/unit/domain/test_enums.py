"""
test_enums.py — Unit tests for src/domain/enums.py

Epic: EPIC-1 | User Story: US-102
Covers acceptance criteria: AC-1 through AC-6
Specification: data_models.md §3
"""
from __future__ import annotations

import pytest

from src.domain.enums import (
    CombatOutcome,
    GamePhase,
    MoveType,
    PlayerSide,
    PlayerType,
    Rank,
    TerrainType,
)


# ---------------------------------------------------------------------------
# US-102 AC-1: FLAG has integer value 0
# ---------------------------------------------------------------------------


class TestRankFlagValue:
    """AC-1: Rank.FLAG.value must equal 0."""

    def test_flag_value_is_zero(self) -> None:
        assert Rank.FLAG.value == 0


# ---------------------------------------------------------------------------
# US-102 AC-2: Exactly 12 Rank members
# ---------------------------------------------------------------------------


class TestRankMemberCount:
    """AC-2: Rank must have exactly 12 members."""

    EXPECTED_MEMBERS = {
        "FLAG", "SPY", "SCOUT", "MINER", "SERGEANT",
        "LIEUTENANT", "CAPTAIN", "MAJOR", "COLONEL",
        "GENERAL", "MARSHAL", "BOMB",
    }

    def test_exactly_twelve_rank_members(self) -> None:
        assert len(Rank) == 12

    def test_all_expected_members_present(self) -> None:
        actual_names = {member.name for member in Rank}
        assert actual_names == self.EXPECTED_MEMBERS


# ---------------------------------------------------------------------------
# US-102 AC-3: BOMB value is 99, not 11
# ---------------------------------------------------------------------------


class TestRankBombValue:
    """AC-3: Rank.BOMB.value must be 99 (not 11)."""

    def test_bomb_value_is_99(self) -> None:
        assert Rank.BOMB.value == 99

    def test_bomb_value_is_not_11(self) -> None:
        assert Rank.BOMB.value != 11


# ---------------------------------------------------------------------------
# US-102 AC-4: MARSHAL rank is higher than GENERAL
# ---------------------------------------------------------------------------


class TestRankComparison:
    """AC-4: Rank.MARSHAL.value > Rank.GENERAL.value."""

    def test_marshal_higher_than_general(self) -> None:
        assert Rank.MARSHAL.value > Rank.GENERAL.value

    @pytest.mark.parametrize(
        "lower, higher",
        [
            (Rank.FLAG, Rank.SPY),
            (Rank.SPY, Rank.SCOUT),
            (Rank.SCOUT, Rank.MINER),
            (Rank.MINER, Rank.SERGEANT),
            (Rank.SERGEANT, Rank.LIEUTENANT),
            (Rank.LIEUTENANT, Rank.CAPTAIN),
            (Rank.CAPTAIN, Rank.MAJOR),
            (Rank.MAJOR, Rank.COLONEL),
            (Rank.COLONEL, Rank.GENERAL),
            (Rank.GENERAL, Rank.MARSHAL),
        ],
        ids=lambda r: r.name if hasattr(r, "name") else str(r),
    )
    def test_rank_ordering(self, lower: Rank, higher: Rank) -> None:
        """Each rank must be strictly higher than the previous one."""
        assert lower.value < higher.value


# ---------------------------------------------------------------------------
# US-102 AC-5: GamePhase has all four members
# ---------------------------------------------------------------------------


class TestGamePhaseMembers:
    """AC-5: GamePhase must contain SETUP, PLAYING, GAME_OVER, MAIN_MENU."""

    def test_setup_exists(self) -> None:
        assert GamePhase.SETUP is not None

    def test_playing_exists(self) -> None:
        assert GamePhase.PLAYING is not None

    def test_game_over_exists(self) -> None:
        assert GamePhase.GAME_OVER is not None

    def test_main_menu_exists(self) -> None:
        assert GamePhase.MAIN_MENU is not None

    def test_exactly_four_phases(self) -> None:
        assert len(GamePhase) == 4


# ---------------------------------------------------------------------------
# Additional: PlayerSide, PlayerType, TerrainType, MoveType, CombatOutcome
# ---------------------------------------------------------------------------


class TestPlayerSide:
    """PlayerSide must have RED and BLUE, and they must be distinct."""

    def test_red_exists(self) -> None:
        assert PlayerSide.RED is not None

    def test_blue_exists(self) -> None:
        assert PlayerSide.BLUE is not None

    def test_red_and_blue_are_different(self) -> None:
        assert PlayerSide.RED != PlayerSide.BLUE

    def test_exactly_two_sides(self) -> None:
        assert len(PlayerSide) == 2


class TestCombatOutcomeMembers:
    """CombatOutcome must have ATTACKER_WINS, DEFENDER_WINS, and DRAW."""

    def test_draw_name(self) -> None:
        """AC from US-102 example: CombatOutcome.DRAW.name == 'DRAW'."""
        assert CombatOutcome.DRAW.name == "DRAW"

    def test_attacker_wins_exists(self) -> None:
        assert CombatOutcome.ATTACKER_WINS is not None

    def test_defender_wins_exists(self) -> None:
        assert CombatOutcome.DEFENDER_WINS is not None

    def test_exactly_three_outcomes(self) -> None:
        assert len(CombatOutcome) == 3


class TestMoveType:
    """MoveType must have MOVE and ATTACK."""

    def test_move_type_has_move(self) -> None:
        assert MoveType.MOVE is not None

    def test_move_type_has_attack(self) -> None:
        assert MoveType.ATTACK is not None

    def test_exactly_two_move_types(self) -> None:
        assert len(MoveType) == 2


class TestTerrainType:
    """TerrainType must have NORMAL and LAKE."""

    def test_normal_exists(self) -> None:
        assert TerrainType.NORMAL is not None

    def test_lake_exists(self) -> None:
        assert TerrainType.LAKE is not None

    def test_exactly_two_terrain_types(self) -> None:
        assert len(TerrainType) == 2


class TestPlayerType:
    """PlayerType must include HUMAN and all AI/network variants."""

    EXPECTED_MEMBERS = {"HUMAN", "AI_EASY", "AI_MEDIUM", "AI_HARD", "NETWORK"}

    def test_all_player_types_present(self) -> None:
        actual = {m.name for m in PlayerType}
        assert actual == self.EXPECTED_MEMBERS


# ---------------------------------------------------------------------------
# US-102 Example assertions (from user story specification)
# ---------------------------------------------------------------------------


class TestUserStoryExamples:
    """Verbatim assertions from US-102 Example block."""

    def test_bomb_value_equals_99(self) -> None:
        assert Rank.BOMB.value == 99

    def test_marshal_value_equals_10(self) -> None:
        assert Rank.MARSHAL.value == 10

    def test_player_sides_are_not_equal(self) -> None:
        assert PlayerSide.RED != PlayerSide.BLUE
