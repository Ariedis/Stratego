"""
test_setup_screen.py — Unit tests for src/presentation/screens/setup_screen.py

Epic: EPIC-4 | User Story: US-405
Covers acceptance criteria: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6
Specification: screen_flow.md §3.6
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.domain.enums import PlayerSide, Rank
from src.domain.piece import Position

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.presentation.screens.setup_screen import SetupScreen
except ImportError:
    SetupScreen = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    SetupScreen is None,
    reason="src.presentation.screens.setup_screen not implemented yet",
    strict=False,
)

# ---------------------------------------------------------------------------
# Standard Stratego army composition — 40 pieces total
# ---------------------------------------------------------------------------

STANDARD_ARMY: list[Rank] = [
    Rank.MARSHAL,      # 1
    Rank.GENERAL,      # 1
    Rank.COLONEL,      # 2
    Rank.COLONEL,
    Rank.MAJOR,        # 3
    Rank.MAJOR,
    Rank.MAJOR,
    Rank.CAPTAIN,      # 4
    Rank.CAPTAIN,
    Rank.CAPTAIN,
    Rank.CAPTAIN,
    Rank.LIEUTENANT,   # 4
    Rank.LIEUTENANT,
    Rank.LIEUTENANT,
    Rank.LIEUTENANT,
    Rank.SERGEANT,     # 4
    Rank.SERGEANT,
    Rank.SERGEANT,
    Rank.SERGEANT,
    Rank.MINER,        # 5
    Rank.MINER,
    Rank.MINER,
    Rank.MINER,
    Rank.MINER,
    Rank.SCOUT,        # 8
    Rank.SCOUT,
    Rank.SCOUT,
    Rank.SCOUT,
    Rank.SCOUT,
    Rank.SCOUT,
    Rank.SCOUT,
    Rank.SCOUT,
    Rank.SPY,          # 1
    Rank.BOMB,         # 6
    Rank.BOMB,
    Rank.BOMB,
    Rank.BOMB,
    Rank.BOMB,
    Rank.BOMB,
    Rank.FLAG,         # 1
]

assert len(STANDARD_ARMY) == 40


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_game_controller() -> MagicMock:
    ctrl = MagicMock()
    ctrl.submit_command = MagicMock()
    ctrl.current_state = MagicMock()
    return ctrl


@pytest.fixture
def mock_screen_manager() -> MagicMock:
    sm = MagicMock()
    sm.push = MagicMock()
    sm.pop = MagicMock()
    sm.replace = MagicMock()
    return sm


@pytest.fixture
def setup_screen(mock_game_controller: MagicMock, mock_screen_manager: MagicMock) -> object:
    """A SetupScreen in its initial state for Red player."""
    screen = SetupScreen(
        game_controller=mock_game_controller,
        screen_manager=mock_screen_manager,
        player_side=PlayerSide.RED,
        army=STANDARD_ARMY,
    )
    screen.on_enter({})
    return screen


# ---------------------------------------------------------------------------
# US-405 AC-1: All 40 pieces appear in the piece tray on open
# ---------------------------------------------------------------------------


class TestTrayInitialState:
    """AC-1: The piece tray contains all 40 pieces when the setup screen opens."""

    def test_tray_has_forty_pieces_on_enter(self, setup_screen: object) -> None:
        """piece_tray has exactly 40 pieces after on_enter."""
        assert len(setup_screen.piece_tray) == 40  # type: ignore[union-attr]

    def test_tray_contains_all_required_ranks(self, setup_screen: object) -> None:
        """piece_tray contains all mandatory ranks from the standard army."""
        tray_ranks = [p.rank for p in setup_screen.piece_tray]  # type: ignore[union-attr]
        assert Rank.FLAG in tray_ranks
        assert Rank.MARSHAL in tray_ranks
        assert tray_ranks.count(Rank.BOMB) == 6
        assert tray_ranks.count(Rank.SCOUT) == 8

    def test_tray_is_initially_sorted_by_rank(self, setup_screen: object) -> None:
        """Tray pieces are sorted by rank (ascending or descending, consistently)."""
        tray = list(setup_screen.piece_tray)  # type: ignore[union-attr]
        ranks = [p.rank for p in tray]
        assert ranks == sorted(ranks) or ranks == sorted(ranks, reverse=True)


# ---------------------------------------------------------------------------
# US-405 AC-2: Placing a piece on a valid square snaps it to the grid
# ---------------------------------------------------------------------------


class TestPlacePieceOnValidSquare:
    """AC-2: Dropping a piece on a valid setup square removes it from the tray."""

    def test_place_piece_removes_it_from_tray(
        self, setup_screen: object, mock_game_controller: MagicMock
    ) -> None:
        """After a successful placement, tray has 39 pieces."""
        tray_piece = list(setup_screen.piece_tray)[0]  # type: ignore[union-attr]
        valid_pos = Position(9, 0)  # Red setup zone row 9
        setup_screen.place_piece(tray_piece, valid_pos)  # type: ignore[union-attr]
        assert len(setup_screen.piece_tray) == 39  # type: ignore[union-attr]

    def test_place_piece_submits_place_piece_command(
        self, setup_screen: object, mock_game_controller: MagicMock
    ) -> None:
        """A valid placement submits a PlacePiece command to the controller."""
        tray_piece = list(setup_screen.piece_tray)[0]  # type: ignore[union-attr]
        valid_pos = Position(9, 0)
        setup_screen.place_piece(tray_piece, valid_pos)  # type: ignore[union-attr]
        mock_game_controller.submit_command.assert_called_once()

    def test_place_piece_adds_to_placed_pieces(
        self, setup_screen: object, mock_game_controller: MagicMock
    ) -> None:
        """A valid placement is tracked in placed_pieces."""
        tray_piece = list(setup_screen.piece_tray)[0]  # type: ignore[union-attr]
        valid_pos = Position(9, 0)
        setup_screen.place_piece(tray_piece, valid_pos)  # type: ignore[union-attr]
        assert len(setup_screen.placed_pieces) == 1  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-405 AC-3: Invalid drop returns piece to tray
# ---------------------------------------------------------------------------


class TestInvalidDrop:
    """AC-3: Dropping a piece on an invalid square returns it to the tray."""

    def test_invalid_placement_keeps_piece_in_tray(self, setup_screen: object) -> None:
        """Placing on a lake square or opponent zone keeps tray count at 40."""
        tray_piece = list(setup_screen.piece_tray)[0]  # type: ignore[union-attr]
        invalid_pos = Position(4, 2)  # lake square
        setup_screen.place_piece(tray_piece, invalid_pos)  # type: ignore[union-attr]
        assert len(setup_screen.piece_tray) == 40  # type: ignore[union-attr]

    def test_invalid_placement_in_opponents_zone_rejected(self, setup_screen: object) -> None:
        """Red cannot place in Blue's zone (rows 0–3)."""
        tray_piece = list(setup_screen.piece_tray)[0]  # type: ignore[union-attr]
        invalid_pos = Position(2, 3)  # Blue's zone for Red
        setup_screen.place_piece(tray_piece, invalid_pos)  # type: ignore[union-attr]
        assert len(setup_screen.piece_tray) == 40  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-405 AC-4: Auto-arrange places all 40 pieces
# ---------------------------------------------------------------------------


class TestAutoArrange:
    """AC-4: Auto-arrange places all 40 pieces in valid positions."""

    def test_auto_arrange_empties_tray(self, setup_screen: object) -> None:
        """After auto_arrange(), the piece tray is empty."""
        setup_screen.auto_arrange()  # type: ignore[union-attr]
        assert len(setup_screen.piece_tray) == 0  # type: ignore[union-attr]

    def test_auto_arrange_places_forty_pieces(self, setup_screen: object) -> None:
        """auto_arrange() places exactly 40 pieces on the board."""
        setup_screen.auto_arrange()  # type: ignore[union-attr]
        assert len(setup_screen.placed_pieces) == 40  # type: ignore[union-attr]

    def test_auto_arrange_submits_forty_commands(
        self, setup_screen: object, mock_game_controller: MagicMock
    ) -> None:
        """auto_arrange() submits 40 PlacePiece commands to the controller."""
        setup_screen.auto_arrange()  # type: ignore[union-attr]
        assert mock_game_controller.submit_command.call_count == 40

    def test_auto_arrange_all_positions_in_setup_zone(self, setup_screen: object) -> None:
        """All auto-arranged pieces are within Red's setup zone (rows 6–9)."""
        setup_screen.auto_arrange()  # type: ignore[union-attr]
        for piece in setup_screen.placed_pieces:  # type: ignore[union-attr]
            assert 6 <= piece.position.row <= 9


# ---------------------------------------------------------------------------
# US-405 AC-5 & AC-6: Ready button
# ---------------------------------------------------------------------------


class TestReadyButton:
    """AC-5 & AC-6: Ready button only transitions when all 40 pieces are placed."""

    def test_ready_when_all_placed_returns_game_state(self, setup_screen: object) -> None:
        """on_exit() returns data containing initial GameState after all pieces placed."""
        setup_screen.auto_arrange()  # type: ignore[union-attr]
        result = setup_screen.on_exit()  # type: ignore[union-attr]
        assert result is not None
        assert "game_state" in result or "initial_state" in result

    def test_ready_when_not_all_placed_raises_or_returns_none(
        self, setup_screen: object
    ) -> None:
        """Clicking Ready with fewer than 40 pieces should not allow transition."""
        # Arrange only 1 piece
        tray_piece = list(setup_screen.piece_tray)[0]  # type: ignore[union-attr]
        setup_screen.place_piece(tray_piece, Position(9, 0))  # type: ignore[union-attr]
        # is_ready must be False
        assert setup_screen.is_ready is False  # type: ignore[union-attr]

    def test_is_ready_false_with_empty_board(self, setup_screen: object) -> None:
        """is_ready is False when no pieces have been placed."""
        assert setup_screen.is_ready is False  # type: ignore[union-attr]

    def test_is_ready_true_when_all_forty_placed(self, setup_screen: object) -> None:
        """is_ready is True after all 40 pieces are placed."""
        setup_screen.auto_arrange()  # type: ignore[union-attr]
        assert setup_screen.is_ready is True  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Clear button
# ---------------------------------------------------------------------------


class TestClearButton:
    """clear() removes all placed pieces back to the tray."""

    def test_clear_restores_full_tray(self, setup_screen: object) -> None:
        """After placing some pieces and calling clear(), tray has 40 pieces."""
        tray_piece = list(setup_screen.piece_tray)[0]  # type: ignore[union-attr]
        setup_screen.place_piece(tray_piece, Position(9, 0))  # type: ignore[union-attr]
        setup_screen.clear()  # type: ignore[union-attr]
        assert len(setup_screen.piece_tray) == 40  # type: ignore[union-attr]

    def test_clear_empties_placed_pieces(self, setup_screen: object) -> None:
        """After clear(), placed_pieces is empty."""
        setup_screen.auto_arrange()  # type: ignore[union-attr]
        setup_screen.clear()  # type: ignore[union-attr]
        assert len(setup_screen.placed_pieces) == 0  # type: ignore[union-attr]
