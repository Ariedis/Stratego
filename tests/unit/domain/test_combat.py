"""Unit tests for combat resolution logic in src.domain.combat."""

from src.domain.combat import resolve_combat
from src.domain.enums import CombatOutcome, PlayerSide, Rank
from src.domain.piece import Piece
from src.domain.position import Position


def _piece(rank: Rank, side: PlayerSide, row: int = 5, col: int = 0) -> Piece:
    """Helper: construct a minimal Piece for combat tests."""
    return Piece(rank=rank, owner=side, revealed=False, has_moved=False,
                 position=Position(row, col))


RED = PlayerSide.RED
BLUE = PlayerSide.BLUE


class TestSpySpecialAbility:
    """Spy's special ability: kills Marshal only when Spy is the attacker."""

    def test_spy_attacks_marshal_attacker_wins(self) -> None:
        """Spy attacking Marshal → ATTACKER_WINS."""
        result = resolve_combat(_piece(Rank.SPY, RED), _piece(Rank.MARSHAL, BLUE))
        assert result.outcome is CombatOutcome.ATTACKER_WINS

    def test_spy_attacks_marshal_spy_survives(self) -> None:
        """Spy attacking Marshal → spy survives."""
        result = resolve_combat(_piece(Rank.SPY, RED), _piece(Rank.MARSHAL, BLUE))
        assert result.attacker_survived is True
        assert result.defender_survived is False

    def test_marshal_attacks_spy_marshal_wins(self) -> None:
        """Marshal attacking Spy → ATTACKER_WINS (normal rank comparison)."""
        result = resolve_combat(_piece(Rank.MARSHAL, RED), _piece(Rank.SPY, BLUE))
        assert result.outcome is CombatOutcome.ATTACKER_WINS

    def test_spy_attacks_captain_defender_wins(self) -> None:
        """Spy attacking a non-Marshal (Captain) → DEFENDER_WINS."""
        result = resolve_combat(_piece(Rank.SPY, RED), _piece(Rank.CAPTAIN, BLUE))
        assert result.outcome is CombatOutcome.DEFENDER_WINS


class TestBombRules:
    """Bomb immunity except for Miner."""

    def test_non_miner_attacks_bomb_defender_wins(self) -> None:
        """Any non-Miner piece attacking a Bomb → DEFENDER_WINS."""
        for rank in (Rank.SPY, Rank.SCOUT, Rank.CAPTAIN, Rank.MARSHAL):
            result = resolve_combat(_piece(rank, RED), _piece(Rank.BOMB, BLUE))
            assert result.outcome is CombatOutcome.DEFENDER_WINS, f"Failed for {rank}"

    def test_miner_attacks_bomb_attacker_wins(self) -> None:
        """Miner attacking a Bomb → ATTACKER_WINS."""
        result = resolve_combat(_piece(Rank.MINER, RED), _piece(Rank.BOMB, BLUE))
        assert result.outcome is CombatOutcome.ATTACKER_WINS

    def test_miner_attacks_bomb_miner_survives(self) -> None:
        """Miner attacking a Bomb → miner survives, bomb removed."""
        result = resolve_combat(_piece(Rank.MINER, RED), _piece(Rank.BOMB, BLUE))
        assert result.attacker_survived is True
        assert result.defender_survived is False


class TestRankComparison:
    """General rank comparison rules."""

    def test_higher_rank_wins(self) -> None:
        """Higher-ranked attacker wins the engagement."""
        result = resolve_combat(_piece(Rank.GENERAL, RED), _piece(Rank.COLONEL, BLUE))
        assert result.outcome is CombatOutcome.ATTACKER_WINS
        assert result.attacker_survived is True
        assert result.defender_survived is False

    def test_lower_rank_loses(self) -> None:
        """Lower-ranked attacker loses the engagement."""
        result = resolve_combat(_piece(Rank.SCOUT, RED), _piece(Rank.MAJOR, BLUE))
        assert result.outcome is CombatOutcome.DEFENDER_WINS
        assert result.attacker_survived is False
        assert result.defender_survived is True

    def test_equal_ranks_draw(self) -> None:
        """Equal ranks → DRAW and both pieces removed."""
        result = resolve_combat(_piece(Rank.MAJOR, RED), _piece(Rank.MAJOR, BLUE))
        assert result.outcome is CombatOutcome.DRAW
        assert result.attacker_survived is False
        assert result.defender_survived is False


class TestFlagCapture:
    """Any attacker capturing the Flag wins."""

    def test_any_piece_attacks_flag_wins(self) -> None:
        """Any piece attacking Flag → ATTACKER_WINS."""
        for rank in (Rank.SPY, Rank.SCOUT, Rank.MINER, Rank.MARSHAL):
            result = resolve_combat(_piece(rank, RED), _piece(Rank.FLAG, BLUE))
            assert result.outcome is CombatOutcome.ATTACKER_WINS, f"Failed for {rank}"


class TestRevealedAfterCombat:
    """Both pieces must be revealed in the CombatResult."""

    def test_attacker_revealed(self) -> None:
        """CombatResult.attacker has revealed=True."""
        result = resolve_combat(_piece(Rank.CAPTAIN, RED), _piece(Rank.LIEUTENANT, BLUE))
        assert result.attacker.revealed is True

    def test_defender_revealed(self) -> None:
        """CombatResult.defender has revealed=True."""
        result = resolve_combat(_piece(Rank.CAPTAIN, RED), _piece(Rank.LIEUTENANT, BLUE))
        assert result.defender.revealed is True

    def test_both_revealed_on_draw(self) -> None:
        """Both pieces are revealed even in a draw."""
        result = resolve_combat(_piece(Rank.CAPTAIN, RED), _piece(Rank.CAPTAIN, BLUE))
        assert result.attacker.revealed is True
        assert result.defender.revealed is True
