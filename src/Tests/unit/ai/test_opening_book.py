"""
test_opening_book.py — Unit tests for src/ai/opening_book.py

Epic: EPIC-5 | User Story: US-504
Covers acceptance criteria:
  AC-1: HARD returns a valid 40-piece arrangement in rows 6–9 (RED)
  AC-2: EASY returns a random permutation (not the optimal Fortress)
  AC-3: Fortress strategy: Flag in back corner, surrounded by ≥ 3 Bombs
  AC-4: MEDIUM returns different arrangements across calls (some randomisation)
Specification: ai_strategy.md §4.1
"""
from __future__ import annotations

import pytest

try:
    from src.ai.opening_book import OpeningBook
    _OPENING_BOOK_AVAILABLE = True
except ImportError:
    _OPENING_BOOK_AVAILABLE = False
    OpeningBook = None  # type: ignore[assignment]

from src.domain.enums import PlayerSide, PlayerType, Rank
from src.domain.piece import Piece, Position

pytestmark = pytest.mark.xfail(
    not _OPENING_BOOK_AVAILABLE,
    reason="src/ai/opening_book.py not yet implemented",
    strict=False,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_RED_SETUP_ROWS = (6, 7, 8, 9)
_BLUE_SETUP_ROWS = (0, 1, 2, 3)
_FORTRESS_BACK_CORNERS: set[tuple[int, int]] = {(9, 0), (9, 1), (9, 8), (9, 9)}
_TOTAL_PIECES = 40

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_flag_position(setup: dict[Position, Piece]) -> Position | None:
    for pos, piece in setup.items():
        if piece.rank == Rank.FLAG:
            return pos
    return None


def _count_adjacent_bombs(flag_pos: Position, setup: dict[Position, Piece]) -> int:
    """Count Bomb pieces in the 8 squares adjacent to flag_pos (orthogonal + diagonal)."""
    bomb_count = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            neighbour = Position(flag_pos.row + dr, flag_pos.col + dc)
            piece = setup.get(neighbour)
            if piece is not None and piece.rank == Rank.BOMB:
                bomb_count += 1
    return bomb_count


# ---------------------------------------------------------------------------
# US-504 AC-1: HARD difficulty — valid 40-piece arrangement
# ---------------------------------------------------------------------------


class TestHardSetup:
    """AC-1: Hard AI returns a valid 40-piece arrangement covering rows 6–9 for RED."""

    def test_hard_returns_forty_pieces(self) -> None:
        """AC-1: Exactly 40 pieces returned for HARD difficulty."""
        book = OpeningBook()
        setup = book.get_setup(PlayerType.AI_HARD)
        assert len(setup) == _TOTAL_PIECES

    def test_hard_pieces_in_red_setup_zone(self) -> None:
        """AC-1: All pieces occupy valid RED setup rows (6–9)."""
        book = OpeningBook()
        setup = book.get_setup(PlayerType.AI_HARD)
        for pos, piece in setup.items():
            assert pos.row in _RED_SETUP_ROWS, (
                f"Piece {piece.rank.name} at row {pos.row} is outside RED setup zone."
            )

    def test_hard_positions_within_board_bounds(self) -> None:
        """AC-1: All positions lie within the 10×10 board."""
        book = OpeningBook()
        setup = book.get_setup(PlayerType.AI_HARD)
        for pos in setup:
            assert pos.is_valid(), f"Position {pos} is outside the board."

    def test_hard_no_duplicate_positions(self) -> None:
        """AC-1: No two pieces occupy the same square."""
        book = OpeningBook()
        setup = book.get_setup(PlayerType.AI_HARD)
        assert len(setup) == len(set(setup.keys()))

    def test_hard_contains_exactly_one_flag(self) -> None:
        """AC-1: Exactly one FLAG piece in the arrangement."""
        book = OpeningBook()
        setup = book.get_setup(PlayerType.AI_HARD)
        flag_count = sum(1 for p in setup.values() if p.rank == Rank.FLAG)
        assert flag_count == 1

    def test_hard_setup_is_deterministic(self) -> None:
        """AC-1 / HARD: Same arrangement returned on repeated calls (no randomisation)."""
        book = OpeningBook()
        setup_1 = book.get_setup(PlayerType.AI_HARD, strategy="fortress")
        setup_2 = book.get_setup(PlayerType.AI_HARD, strategy="fortress")
        assert setup_1 == setup_2


# ---------------------------------------------------------------------------
# US-504 AC-3: Fortress strategy
# ---------------------------------------------------------------------------


class TestFortressStrategy:
    """AC-3: Fortress setup places Flag in a back corner surrounded by ≥ 3 Bombs."""

    def test_fortress_flag_in_back_row(self) -> None:
        """AC-3: Flag is in row 9 (back row for RED)."""
        book = OpeningBook()
        setup = book.get_setup(PlayerType.AI_HARD, strategy="fortress")
        flag_pos = _get_flag_position(setup)
        assert flag_pos is not None
        assert flag_pos.row == 9, f"Flag at row {flag_pos.row}, expected back row 9."

    def test_fortress_flag_in_corner(self) -> None:
        """AC-3: Flag is in one of the four back corners."""
        book = OpeningBook()
        setup = book.get_setup(PlayerType.AI_HARD, strategy="fortress")
        flag_pos = _get_flag_position(setup)
        assert flag_pos is not None
        assert (flag_pos.row, flag_pos.col) in _FORTRESS_BACK_CORNERS, (
            f"Flag at {flag_pos} is not in a back corner."
        )

    def test_fortress_flag_surrounded_by_at_least_three_bombs(self) -> None:
        """AC-3: Flag has ≥ 3 adjacent Bombs."""
        book = OpeningBook()
        setup = book.get_setup(PlayerType.AI_HARD, strategy="fortress")
        flag_pos = _get_flag_position(setup)
        assert flag_pos is not None
        bomb_count = _count_adjacent_bombs(flag_pos, setup)
        assert bomb_count >= 3, (
            f"Flag at {flag_pos} is only surrounded by {bomb_count} Bombs; expected ≥ 3."
        )


# ---------------------------------------------------------------------------
# US-504 AC-2: EASY difficulty — random permutation
# ---------------------------------------------------------------------------


class TestEasySetup:
    """AC-2: EASY returns a randomly permuted base setup (still valid, but randomised)."""

    def test_easy_returns_forty_pieces(self) -> None:
        """AC-2: Exactly 40 pieces returned for EASY difficulty."""
        book = OpeningBook()
        setup = book.get_setup(PlayerType.AI_EASY)
        assert len(setup) == _TOTAL_PIECES

    def test_easy_pieces_in_red_setup_zone(self) -> None:
        """AC-2: All EASY pieces occupy RED setup rows 6–9."""
        book = OpeningBook()
        setup = book.get_setup(PlayerType.AI_EASY)
        for pos, piece in setup.items():
            assert pos.row in _RED_SETUP_ROWS

    def test_easy_returns_different_setups_across_calls(self) -> None:
        """AC-2: EASY setups differ across multiple calls (random permutation)."""
        book = OpeningBook()
        setups = [book.get_setup(PlayerType.AI_EASY) for _ in range(10)]
        unique_setups = {frozenset((pos, piece.rank) for pos, piece in s.items()) for s in setups}
        # With 40 pieces randomly placed, we expect at least 2 distinct arrangements
        assert len(unique_setups) >= 2, (
            "EASY difficulty should produce different setups across calls."
        )


# ---------------------------------------------------------------------------
# US-504 AC-4: MEDIUM difficulty — some randomisation
# ---------------------------------------------------------------------------


class TestMediumSetup:
    """AC-4: MEDIUM returns different arrangements across calls (30% perturbation)."""

    def test_medium_returns_forty_pieces(self) -> None:
        """AC-4: Exactly 40 pieces returned for MEDIUM difficulty."""
        book = OpeningBook()
        setup = book.get_setup(PlayerType.AI_MEDIUM)
        assert len(setup) == _TOTAL_PIECES

    def test_medium_pieces_in_red_setup_zone(self) -> None:
        """AC-4: All MEDIUM pieces occupy RED setup rows 6–9."""
        book = OpeningBook()
        setup = book.get_setup(PlayerType.AI_MEDIUM)
        for pos, piece in setup.items():
            assert pos.row in _RED_SETUP_ROWS

    def test_medium_returns_at_least_two_distinct_setups_in_five_calls(self) -> None:
        """AC-4: At least 2 different arrangements observed in 5 calls."""
        book = OpeningBook()
        setups = [book.get_setup(PlayerType.AI_MEDIUM) for _ in range(5)]
        unique_setups = {frozenset((pos, piece.rank) for pos, piece in s.items()) for s in setups}
        assert len(unique_setups) >= 2, (
            "MEDIUM difficulty should occasionally produce different arrangements."
        )


# ---------------------------------------------------------------------------
# Blue-side mirroring tests (bonus)
# ---------------------------------------------------------------------------


class TestBlueSideMirroring:
    """Setups returned for BLUE side must occupy rows 0–3."""

    @pytest.mark.parametrize(
        "difficulty",
        [PlayerType.AI_EASY, PlayerType.AI_MEDIUM, PlayerType.AI_HARD],
        ids=["easy", "medium", "hard"],
    )
    def test_blue_setup_occupies_rows_0_to_3(self, difficulty: PlayerType) -> None:
        """get_setup() for BLUE side places all pieces in rows 0–3."""
        book = OpeningBook()
        setup = book.get_setup(difficulty, side=PlayerSide.BLUE)
        for pos, piece in setup.items():
            assert pos.row in _BLUE_SETUP_ROWS, (
                f"{piece.rank.name} at row {pos.row} is outside BLUE setup zone."
            )
