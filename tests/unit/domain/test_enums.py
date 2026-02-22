"""Unit tests for all domain enumerations in src.domain.enums."""

from src.domain.enums import (
    CombatOutcome,
    GamePhase,
    MoveType,
    PlayerSide,
    PlayerType,
    Rank,
    TerrainType,
)


class TestRank:
    """Tests for the Rank IntEnum."""

    def test_flag_value(self) -> None:
        """FLAG has integer value 0."""
        assert Rank.FLAG.value == 0

    def test_spy_value(self) -> None:
        """SPY has integer value 1."""
        assert Rank.SPY.value == 1

    def test_scout_value(self) -> None:
        """SCOUT has integer value 2."""
        assert Rank.SCOUT.value == 2

    def test_miner_value(self) -> None:
        """MINER has integer value 3."""
        assert Rank.MINER.value == 3

    def test_sergeant_value(self) -> None:
        """SERGEANT has integer value 4."""
        assert Rank.SERGEANT.value == 4

    def test_lieutenant_value(self) -> None:
        """LIEUTENANT has integer value 5."""
        assert Rank.LIEUTENANT.value == 5

    def test_captain_value(self) -> None:
        """CAPTAIN has integer value 6."""
        assert Rank.CAPTAIN.value == 6

    def test_major_value(self) -> None:
        """MAJOR has integer value 7."""
        assert Rank.MAJOR.value == 7

    def test_colonel_value(self) -> None:
        """COLONEL has integer value 8."""
        assert Rank.COLONEL.value == 8

    def test_general_value(self) -> None:
        """GENERAL has integer value 9."""
        assert Rank.GENERAL.value == 9

    def test_marshal_value(self) -> None:
        """MARSHAL has integer value 10."""
        assert Rank.MARSHAL.value == 10

    def test_bomb_value(self) -> None:
        """BOMB has integer value 99."""
        assert Rank.BOMB.value == 99

    def test_marshal_greater_than_general(self) -> None:
        """MARSHAL ranks above GENERAL."""
        assert Rank.MARSHAL.value > Rank.GENERAL.value

    def test_rank_member_count(self) -> None:
        """Rank has exactly 12 members."""
        assert len(Rank) == 12


class TestPlayerSide:
    """Tests for the PlayerSide enum."""

    def test_red_and_blue_exist(self) -> None:
        """RED and BLUE are valid members."""
        assert PlayerSide.RED is not None
        assert PlayerSide.BLUE is not None

    def test_member_count(self) -> None:
        """PlayerSide has exactly 2 members."""
        assert len(PlayerSide) == 2


class TestPlayerType:
    """Tests for the PlayerType enum."""

    def test_all_types_exist(self) -> None:
        """All five player types are present."""
        assert PlayerType.HUMAN is not None
        assert PlayerType.AI_EASY is not None
        assert PlayerType.AI_MEDIUM is not None
        assert PlayerType.AI_HARD is not None
        assert PlayerType.NETWORK is not None

    def test_member_count(self) -> None:
        """PlayerType has exactly 5 members."""
        assert len(PlayerType) == 5


class TestGamePhase:
    """Tests for the GamePhase enum."""

    def test_all_phases_exist(self) -> None:
        """All four game phases are present."""
        assert GamePhase.MAIN_MENU is not None
        assert GamePhase.SETUP is not None
        assert GamePhase.PLAYING is not None
        assert GamePhase.GAME_OVER is not None

    def test_member_count(self) -> None:
        """GamePhase has exactly 4 members."""
        assert len(GamePhase) == 4


class TestTerrainType:
    """Tests for the TerrainType enum."""

    def test_normal_and_lake_exist(self) -> None:
        """NORMAL and LAKE are valid members."""
        assert TerrainType.NORMAL is not None
        assert TerrainType.LAKE is not None

    def test_member_count(self) -> None:
        """TerrainType has exactly 2 members."""
        assert len(TerrainType) == 2


class TestMoveType:
    """Tests for the MoveType enum."""

    def test_move_and_attack_exist(self) -> None:
        """MOVE and ATTACK are valid members."""
        assert MoveType.MOVE is not None
        assert MoveType.ATTACK is not None

    def test_member_count(self) -> None:
        """MoveType has exactly 2 members."""
        assert len(MoveType) == 2


class TestCombatOutcome:
    """Tests for the CombatOutcome enum."""

    def test_all_outcomes_exist(self) -> None:
        """All three combat outcomes are present."""
        assert CombatOutcome.ATTACKER_WINS is not None
        assert CombatOutcome.DEFENDER_WINS is not None
        assert CombatOutcome.DRAW is not None

    def test_member_count(self) -> None:
        """CombatOutcome has exactly 3 members."""
        assert len(CombatOutcome) == 3
