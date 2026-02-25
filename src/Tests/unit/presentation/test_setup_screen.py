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


# ---------------------------------------------------------------------------
# Tray selection (wireframe §Piece Tray)
# ---------------------------------------------------------------------------


class TestTraySelection:
    """Tests for rank-based tray selection."""

    def test_selected_rank_is_none_on_enter(self, setup_screen: object) -> None:
        """selected_rank is None immediately after on_enter."""
        assert setup_screen._selected_rank is None  # type: ignore[union-attr]

    def test_find_tray_piece_returns_first_when_no_selection(
        self, setup_screen: object
    ) -> None:
        """_find_tray_piece returns the first tray piece when no rank is selected."""
        piece = setup_screen._find_tray_piece()  # type: ignore[union-attr]
        assert piece is setup_screen.piece_tray[0]  # type: ignore[union-attr]

    def test_find_tray_piece_returns_matching_rank(self, setup_screen: object) -> None:
        """_find_tray_piece returns a piece with the selected rank."""
        from src.domain.enums import Rank
        setup_screen._selected_rank = Rank.SCOUT  # type: ignore[union-attr]
        piece = setup_screen._find_tray_piece()  # type: ignore[union-attr]
        assert piece is not None
        assert piece.rank == Rank.SCOUT  # type: ignore[union-attr]

    def test_find_tray_piece_falls_back_when_rank_exhausted(
        self, setup_screen: object
    ) -> None:
        """When selected rank is depleted, _find_tray_piece returns the first piece."""
        from src.domain.enums import Rank
        setup_screen._selected_rank = Rank.FLAG  # type: ignore[union-attr]
        # Exhaust FLAG from the tray by placing it.
        flag_pieces = [
            p for p in setup_screen.piece_tray  # type: ignore[union-attr]
            if p.rank == Rank.FLAG
        ]
        for fp in flag_pieces:
            setup_screen.place_piece(fp, Position(9, 9))  # type: ignore[union-attr]
        # Selected rank no longer in tray: fallback to first piece.
        piece = setup_screen._find_tray_piece()  # type: ignore[union-attr]
        assert piece is not None
        assert piece is setup_screen.piece_tray[0]  # type: ignore[union-attr]

    def test_cycle_tray_selection_advances(self, setup_screen: object) -> None:
        """_cycle_tray_selection(1) moves to the next available rank."""
        from src.presentation.screens.setup_screen import _TRAY_ORDER
        setup_screen._selected_rank = _TRAY_ORDER[0]  # type: ignore[union-attr]
        setup_screen._cycle_tray_selection(1)  # type: ignore[union-attr]
        assert setup_screen._selected_rank == _TRAY_ORDER[1]  # type: ignore[union-attr]

    def test_cycle_tray_selection_wraps(self, setup_screen: object) -> None:
        """_cycle_tray_selection wraps from the last rank back to the first."""
        from src.presentation.screens.setup_screen import _TRAY_ORDER
        available = [
            r for r in _TRAY_ORDER
            if any(p.rank == r for p in setup_screen.piece_tray)  # type: ignore[union-attr]
        ]
        setup_screen._selected_rank = available[-1]  # type: ignore[union-attr]
        setup_screen._cycle_tray_selection(1)  # type: ignore[union-attr]
        assert setup_screen._selected_rank == available[0]  # type: ignore[union-attr]

    def test_cycle_tray_selection_backward(self, setup_screen: object) -> None:
        """_cycle_tray_selection(-1) moves to the previous rank."""
        from src.presentation.screens.setup_screen import _TRAY_ORDER
        setup_screen._selected_rank = _TRAY_ORDER[1]  # type: ignore[union-attr]
        setup_screen._cycle_tray_selection(-1)  # type: ignore[union-attr]
        assert setup_screen._selected_rank == _TRAY_ORDER[0]  # type: ignore[union-attr]

    def test_cycle_initialises_when_none(self, setup_screen: object) -> None:
        """_cycle_tray_selection sets first available rank when selection is None."""
        from src.presentation.screens.setup_screen import _TRAY_ORDER
        assert setup_screen._selected_rank is None  # type: ignore[union-attr]
        setup_screen._cycle_tray_selection(1)  # type: ignore[union-attr]
        available = [
            r for r in _TRAY_ORDER
            if any(p.rank == r for p in setup_screen.piece_tray)  # type: ignore[union-attr]
        ]
        assert setup_screen._selected_rank == available[0]  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Invalid-cell flash (wireframe annotation 4)
# ---------------------------------------------------------------------------


class TestInvalidCellFlash:
    """Annotation 4: placing outside the setup zone triggers a flash."""

    def test_invalid_flash_cells_empty_on_enter(self, setup_screen: object) -> None:
        """No flash cells are active immediately after on_enter."""
        assert setup_screen._invalid_flash_cells == {}  # type: ignore[union-attr]

    def test_update_decrements_flash_timer(self, setup_screen: object) -> None:
        """update() reduces the remaining time on an active flash cell."""
        setup_screen._invalid_flash_cells[(0, 0)] = 0.5  # type: ignore[union-attr]
        setup_screen.update(0.1)  # type: ignore[union-attr]
        assert setup_screen._invalid_flash_cells[(0, 0)] == pytest.approx(0.4)  # type: ignore[union-attr]

    def test_update_removes_expired_flash_cell(self, setup_screen: object) -> None:
        """update() removes a flash cell whose timer has reached zero."""
        setup_screen._invalid_flash_cells[(3, 3)] = 0.0  # type: ignore[union-attr]
        setup_screen.update(0.1)  # type: ignore[union-attr]
        assert (3, 3) not in setup_screen._invalid_flash_cells  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Handover overlay (wireframe §Player Handover Overlay)
# ---------------------------------------------------------------------------


class TestHandoverOverlay:
    """Handover overlay is shown when Player 1 clicks Ready in 2-player mode."""

    def _make_two_player_screen(
        self,
        mock_game_controller: MagicMock,
        mock_screen_manager: MagicMock,
    ) -> object:
        """Return a SetupScreen wired for a 2-player game."""
        from src.domain.enums import PlayerType

        red_player = MagicMock()
        red_player.side = PlayerSide.RED
        red_player.player_type = PlayerType.HUMAN
        red_player.pieces_remaining = []

        blue_player = MagicMock()
        blue_player.side = PlayerSide.BLUE
        blue_player.player_type = PlayerType.HUMAN
        blue_player.pieces_remaining = []

        mock_game_controller.current_state = MagicMock()
        mock_game_controller.current_state.players = [red_player, blue_player]

        screen = SetupScreen(
            game_controller=mock_game_controller,
            screen_manager=mock_screen_manager,
            player_side=PlayerSide.RED,
            army=STANDARD_ARMY,
            event_bus=MagicMock(),
            renderer=MagicMock(),
        )
        screen.on_enter({})
        return screen

    def test_overlay_not_shown_initially(
        self,
        mock_game_controller: MagicMock,
        mock_screen_manager: MagicMock,
    ) -> None:
        """Handover overlay is hidden when the screen first opens."""
        screen = self._make_two_player_screen(mock_game_controller, mock_screen_manager)
        assert screen._show_handover_overlay is False  # type: ignore[union-attr]

    def test_overlay_shown_after_ready_in_two_player(
        self,
        mock_game_controller: MagicMock,
        mock_screen_manager: MagicMock,
    ) -> None:
        """_show_handover_overlay becomes True when Player 1 clicks Ready."""
        from src.domain.enums import PlayerType

        blue_player = MagicMock()
        blue_player.side = PlayerSide.BLUE
        blue_player.player_type = PlayerType.HUMAN
        blue_player.pieces_remaining = []

        red_player = MagicMock()
        red_player.side = PlayerSide.RED
        red_player.player_type = PlayerType.HUMAN
        red_player.pieces_remaining = []

        mock_game_controller.current_state = MagicMock()
        mock_game_controller.current_state.players = [red_player, blue_player]

        screen = SetupScreen(
            game_controller=mock_game_controller,
            screen_manager=mock_screen_manager,
            player_side=PlayerSide.RED,
            army=STANDARD_ARMY,
            event_bus=MagicMock(),
            renderer=MagicMock(),
        )
        screen.on_enter({})
        screen.auto_arrange()  # type: ignore[union-attr]
        screen._on_ready()  # type: ignore[union-attr]
        assert screen._show_handover_overlay is True  # type: ignore[union-attr]
        # screen_manager.replace should NOT have been called yet.
        mock_screen_manager.replace.assert_not_called()

    def test_dismiss_handover_overlay_calls_replace(
        self,
        mock_game_controller: MagicMock,
        mock_screen_manager: MagicMock,
    ) -> None:
        """_dismiss_handover_overlay() hides the overlay and transitions screens."""
        from src.domain.enums import PlayerType

        blue_player = MagicMock()
        blue_player.side = PlayerSide.BLUE
        blue_player.player_type = PlayerType.HUMAN
        blue_player.pieces_remaining = []

        red_player = MagicMock()
        red_player.side = PlayerSide.RED
        red_player.player_type = PlayerType.HUMAN
        red_player.pieces_remaining = []

        mock_game_controller.current_state = MagicMock()
        mock_game_controller.current_state.players = [red_player, blue_player]

        screen = SetupScreen(
            game_controller=mock_game_controller,
            screen_manager=mock_screen_manager,
            player_side=PlayerSide.RED,
            army=STANDARD_ARMY,
            event_bus=MagicMock(),
            renderer=MagicMock(),
        )
        screen.on_enter({})
        screen.auto_arrange()  # type: ignore[union-attr]
        screen._on_ready()  # type: ignore[union-attr]
        assert screen._show_handover_overlay is True  # type: ignore[union-attr]

        screen._dismiss_handover_overlay()  # type: ignore[union-attr]
        assert screen._show_handover_overlay is False  # type: ignore[union-attr]
        mock_screen_manager.replace.assert_called_once()
