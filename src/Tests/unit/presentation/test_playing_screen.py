"""
test_playing_screen.py — Unit tests for PlayingScreen.

Epic: EPIC-4 | User Story: US-406
Covers: on_enter, on_exit, event handling, piece selection, move submission,
        quit-to-menu, game over transition.
Specification: screen_flow.md §3.7
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.application.event_bus import EventBus
from src.domain.enums import PlayerSide, Rank
from src.domain.piece import Piece, Position

try:
    from src.presentation.screens.playing_screen import PlayingScreen
except ImportError:
    PlayingScreen = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    PlayingScreen is None,
    reason="PlayingScreen not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def mock_controller() -> MagicMock:
    ctrl = MagicMock()
    state = MagicMock()
    state.active_player = PlayerSide.RED
    state.turn_number = 0
    state.board = MagicMock()
    # Default: no piece on any square
    sq = MagicMock()
    sq.piece = None
    state.board.get_square.return_value = sq
    ctrl.current_state = state
    return ctrl


@pytest.fixture
def mock_screen_manager() -> MagicMock:
    sm = MagicMock()
    sm.push = MagicMock()
    sm.pop = MagicMock()
    sm.replace = MagicMock()
    return sm


@pytest.fixture
def mock_renderer() -> MagicMock:
    r = MagicMock()
    r.render = MagicMock()
    return r


@pytest.fixture
def playing_screen(
    mock_controller: MagicMock,
    mock_screen_manager: MagicMock,
    event_bus: EventBus,
    mock_renderer: MagicMock,
) -> object:
    screen = PlayingScreen(
        controller=mock_controller,
        screen_manager=mock_screen_manager,
        event_bus=event_bus,
        renderer=mock_renderer,
        viewing_player=PlayerSide.RED,
    )
    screen.on_enter({})
    return screen


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestPlayingScreenLifecycle:
    """Tests for on_enter / on_exit."""

    def test_on_enter_does_not_raise(
        self,
        mock_controller: MagicMock,
        mock_screen_manager: MagicMock,
        event_bus: EventBus,
        mock_renderer: MagicMock,
    ) -> None:
        screen = PlayingScreen(
            controller=mock_controller,
            screen_manager=mock_screen_manager,
            event_bus=event_bus,
            renderer=mock_renderer,
        )
        screen.on_enter({})

    def test_on_exit_returns_game_state(self, playing_screen: object) -> None:
        result = playing_screen.on_exit()  # type: ignore[union-attr]
        assert "game_state" in result

    def test_on_enter_accepts_viewing_player_override(
        self,
        mock_controller: MagicMock,
        mock_screen_manager: MagicMock,
        event_bus: EventBus,
        mock_renderer: MagicMock,
    ) -> None:
        screen = PlayingScreen(
            controller=mock_controller,
            screen_manager=mock_screen_manager,
            event_bus=event_bus,
            renderer=mock_renderer,
        )
        screen.on_enter({"viewing_player": PlayerSide.BLUE})
        assert screen._viewing_player == PlayerSide.BLUE  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Render / update
# ---------------------------------------------------------------------------


class TestPlayingScreenRender:
    """Tests for render and update."""

    def test_render_with_none_does_not_raise(self, playing_screen: object) -> None:
        playing_screen.render(None)  # type: ignore[union-attr]

    def test_update_does_not_raise(self, playing_screen: object) -> None:
        playing_screen.update(0.016)  # type: ignore[union-attr]

    def test_update_decrements_invalid_flash(self, playing_screen: object) -> None:
        playing_screen._invalid_flash = 1.0  # type: ignore[union-attr]
        playing_screen.update(0.5)  # type: ignore[union-attr]
        assert playing_screen._invalid_flash == pytest.approx(0.5)  # type: ignore[union-attr]

    def test_update_clamps_flash_to_zero(self, playing_screen: object) -> None:
        playing_screen._invalid_flash = 0.1  # type: ignore[union-attr]
        playing_screen.update(1.0)  # type: ignore[union-attr]
        assert playing_screen._invalid_flash == 0.0  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Event handling — null/quit
# ---------------------------------------------------------------------------


class TestPlayingScreenEvents:
    """Tests for handle_event."""

    def test_handle_event_none_does_not_raise(self, playing_screen: object) -> None:
        playing_screen.handle_event(None)  # type: ignore[union-attr]

    def test_right_click_clears_selection(self, playing_screen: object) -> None:
        playing_screen._selected_pos = Position(5, 5)  # type: ignore[union-attr]
        event = MagicMock()
        event.type = 1025  # MOUSEBUTTONDOWN
        event.button = 3
        playing_screen.handle_event(event)  # type: ignore[union-attr]
        assert playing_screen._selected_pos is None  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Piece selection
# ---------------------------------------------------------------------------


class TestPieceSelection:
    """Tests for click-to-select logic."""

    def test_click_on_own_piece_selects_it(
        self,
        mock_controller: MagicMock,
        mock_screen_manager: MagicMock,
        event_bus: EventBus,
        mock_renderer: MagicMock,
    ) -> None:
        """Clicking on an own piece should select it."""
        piece = Piece(
            rank=Rank.MARSHAL,
            owner=PlayerSide.RED,
            revealed=True,
            has_moved=False,
            position=Position(9, 0),
        )
        sq_with_piece = MagicMock()
        sq_with_piece.piece = piece

        mock_controller.current_state.active_player = PlayerSide.RED
        mock_controller.current_state.board.get_square.return_value = sq_with_piece

        screen = PlayingScreen(
            controller=mock_controller,
            screen_manager=mock_screen_manager,
            event_bus=event_bus,
            renderer=mock_renderer,
        )
        screen.on_enter({})
        screen._cell_w = 76  # type: ignore[union-attr]
        screen._cell_h = 76  # type: ignore[union-attr]

        # Simulate left-click at the centre of square (9, 0)
        screen._handle_left_click((38, 9 * 76 + 38))  # type: ignore[union-attr]
        assert screen._selected_pos == Position(9, 0)  # type: ignore[union-attr]

    def test_click_on_opponent_piece_does_not_select(
        self,
        mock_controller: MagicMock,
        mock_screen_manager: MagicMock,
        event_bus: EventBus,
        mock_renderer: MagicMock,
    ) -> None:
        """Clicking on an opponent's piece without a prior selection is ignored."""
        piece = Piece(
            rank=Rank.MARSHAL,
            owner=PlayerSide.BLUE,
            revealed=False,
            has_moved=False,
            position=Position(0, 0),
        )
        sq_with_piece = MagicMock()
        sq_with_piece.piece = piece

        mock_controller.current_state.active_player = PlayerSide.RED
        mock_controller.current_state.board.get_square.return_value = sq_with_piece

        screen = PlayingScreen(
            controller=mock_controller,
            screen_manager=mock_screen_manager,
            event_bus=event_bus,
            renderer=mock_renderer,
        )
        screen.on_enter({})
        screen._cell_w = 76  # type: ignore[union-attr]
        screen._cell_h = 76  # type: ignore[union-attr]

        screen._handle_left_click((38, 38))  # type: ignore[union-attr]
        assert screen._selected_pos is None  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Domain event handlers
# ---------------------------------------------------------------------------


class TestPlayingScreenDomainEvents:
    """Tests for domain event handler callbacks."""

    def test_on_piece_moved_clears_selection(self, playing_screen: object) -> None:
        from src.application.events import PieceMoved
        from src.domain.enums import Rank

        playing_screen._selected_pos = Position(5, 5)  # type: ignore[union-attr]
        piece = Piece(
            rank=Rank.SCOUT,
            owner=PlayerSide.RED,
            revealed=True,
            has_moved=True,
            position=Position(6, 5),
        )
        playing_screen._on_piece_moved(  # type: ignore[union-attr]
            PieceMoved(from_pos=Position(5, 5), to_pos=Position(6, 5), piece=piece)
        )
        assert playing_screen._selected_pos is None  # type: ignore[union-attr]

    def test_on_piece_moved_updates_last_move_text(self, playing_screen: object) -> None:
        from src.application.events import PieceMoved
        from src.domain.enums import Rank

        piece = Piece(
            rank=Rank.SERGEANT,
            owner=PlayerSide.RED,
            revealed=True,
            has_moved=True,
            position=Position(6, 3),
        )
        playing_screen._on_piece_moved(  # type: ignore[union-attr]
            PieceMoved(from_pos=Position(6, 3), to_pos=Position(5, 3), piece=piece)
        )
        last = playing_screen._last_move_text  # type: ignore[union-attr]
        assert "RED" in last or "red" in last.lower()
        assert "→" in last

    def test_on_combat_resolved_tracks_captured_by_red(self, playing_screen: object) -> None:
        from src.application.events import CombatResolved
        from src.domain.enums import Rank

        attacker = Piece(
            rank=Rank.MARSHAL,
            owner=PlayerSide.RED,
            revealed=True,
            has_moved=True,
            position=Position(0, 0),
        )
        defender = Piece(
            rank=Rank.GENERAL,
            owner=PlayerSide.BLUE,
            revealed=True,
            has_moved=False,
            position=Position(0, 1),
        )
        playing_screen._on_combat_resolved(  # type: ignore[union-attr]
            CombatResolved(attacker=attacker, defender=defender, winner=PlayerSide.RED)
        )
        assert "Ge" in playing_screen._captured_by_red  # type: ignore[union-attr]

    def test_on_combat_resolved_tracks_captured_by_blue(self, playing_screen: object) -> None:
        from src.application.events import CombatResolved
        from src.domain.enums import Rank

        attacker = Piece(
            rank=Rank.COLONEL,
            owner=PlayerSide.RED,
            revealed=True,
            has_moved=True,
            position=Position(0, 0),
        )
        defender = Piece(
            rank=Rank.GENERAL,
            owner=PlayerSide.BLUE,
            revealed=True,
            has_moved=False,
            position=Position(0, 1),
        )
        playing_screen._on_combat_resolved(  # type: ignore[union-attr]
            CombatResolved(attacker=attacker, defender=defender, winner=PlayerSide.BLUE)
        )
        assert "Co" in playing_screen._captured_by_blue  # type: ignore[union-attr]

    def test_on_invalid_move_sets_flash(self, playing_screen: object) -> None:
        from src.application.events import InvalidMove
        from src.domain.enums import MoveType
        from src.domain.move import Move

        piece = Piece(
            rank=Rank.SCOUT,
            owner=PlayerSide.RED,
            revealed=False,
            has_moved=False,
            position=Position(5, 5),
        )
        move = Move(
            piece=piece,
            from_pos=Position(5, 5),
            to_pos=Position(6, 5),
            move_type=MoveType.MOVE,
        )
        playing_screen._on_invalid_move(  # type: ignore[union-attr]
            InvalidMove(player=PlayerSide.RED, move=move, reason="Test")
        )
        assert playing_screen._invalid_flash > 0  # type: ignore[union-attr]

    def test_on_turn_changed_clears_selection(self, playing_screen: object) -> None:
        from src.application.events import TurnChanged

        playing_screen._selected_pos = Position(5, 5)  # type: ignore[union-attr]
        playing_screen._on_turn_changed(TurnChanged(active_player=PlayerSide.BLUE))  # type: ignore[union-attr]
        assert playing_screen._selected_pos is None  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Quit-to-menu stack clearing
# ---------------------------------------------------------------------------


class TestQuitToMenu:
    """Tests for _on_quit_to_menu using the public stack property."""

    def test_quit_pops_all_screens_above_root(
        self,
        mock_controller: MagicMock,
        event_bus: EventBus,
        mock_renderer: MagicMock,
    ) -> None:
        """_on_quit_to_menu() should pop until only the root screen remains."""
        from src.application.screen_manager import ScreenManager
        from src.presentation.screens.base import Screen

        class _Stub(Screen):
            def on_enter(self, data: dict) -> None: ...  # type: ignore[override]
            def on_exit(self) -> dict: return {}
            def render(self, surface: object) -> None: ...
            def handle_event(self, event: object) -> None: ...
            def update(self, dt: float) -> None: ...

        sm = ScreenManager()
        root = _Stub()
        sm.push(root)
        sm.push(_Stub())
        sm.push(_Stub())

        screen = PlayingScreen(
            controller=mock_controller,
            screen_manager=sm,
            event_bus=event_bus,
            renderer=mock_renderer,
        )
        screen.on_enter({})
        screen._on_quit_to_menu()  # type: ignore[union-attr]
        assert len(sm.stack) == 1
        assert sm.stack[0] is root


# ---------------------------------------------------------------------------
# Undo button
# ---------------------------------------------------------------------------


class TestUndoButton:
    """Tests for the Undo button feature."""

    def test_undo_enabled_exposes_attribute(
        self,
        mock_controller: MagicMock,
        mock_screen_manager: MagicMock,
        event_bus: EventBus,
        mock_renderer: MagicMock,
    ) -> None:
        screen = PlayingScreen(
            controller=mock_controller,
            screen_manager=mock_screen_manager,
            event_bus=event_bus,
            renderer=mock_renderer,
            undo_enabled=True,
        )
        assert screen._undo_enabled is True  # type: ignore[union-attr]

    def test_undo_disabled_by_default(self, playing_screen: object) -> None:
        assert playing_screen._undo_enabled is False  # type: ignore[union-attr]
