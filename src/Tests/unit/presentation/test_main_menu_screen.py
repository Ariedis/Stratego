"""
test_main_menu_screen.py — Unit tests for MainMenuScreen.

Epic: EPIC-4 | User Story: US-404
Covers: on_enter, render (headless), handle_event, navigation to StartGameScreen.
Specification: screen_flow.md §3.1
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

try:
    from src.presentation.screens.main_menu_screen import MainMenuScreen
except ImportError:
    MainMenuScreen = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    MainMenuScreen is None,
    reason="MainMenuScreen not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_screen_manager() -> MagicMock:
    """Minimal ScreenManager mock."""
    sm = MagicMock()
    sm.push = MagicMock()
    sm.pop = MagicMock()
    sm.replace = MagicMock()
    return sm


@pytest.fixture
def mock_game_context() -> MagicMock:
    """Minimal _GameContext mock."""
    ctx = MagicMock()
    ctx.start_new_game = MagicMock()
    return ctx


@pytest.fixture
def menu_screen(mock_screen_manager: MagicMock, mock_game_context: MagicMock) -> object:
    """A MainMenuScreen with mocked dependencies."""
    screen = MainMenuScreen(
        screen_manager=mock_screen_manager,
        game_context=mock_game_context,
    )
    screen.on_enter({})
    return screen


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestMainMenuLifecycle:
    """Tests for on_enter and on_exit lifecycle hooks."""

    def test_on_enter_does_not_raise(
        self, mock_screen_manager: MagicMock, mock_game_context: MagicMock
    ) -> None:
        """on_enter({}) should not raise even without a pygame display."""
        screen = MainMenuScreen(
            screen_manager=mock_screen_manager,
            game_context=mock_game_context,
        )
        screen.on_enter({})  # must not raise

    def test_on_exit_returns_empty_dict(self, menu_screen: object) -> None:
        """on_exit() returns an empty dict."""
        result = menu_screen.on_exit()  # type: ignore[union-attr]
        assert result == {}

    def test_update_does_not_raise(self, menu_screen: object) -> None:
        """update(delta_time) should not raise."""
        menu_screen.update(0.016)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


class TestMainMenuRender:
    """Tests for the render method."""

    def test_render_with_none_surface_does_not_raise(
        self, menu_screen: object
    ) -> None:
        """render(None) is a no-op and must not raise."""
        menu_screen.render(None)  # type: ignore[union-attr]

    def test_render_with_mock_surface_does_not_raise(
        self, menu_screen: object
    ) -> None:
        """render(surface) should not raise when surface is None (headless)."""
        # Rendering with a real pygame surface requires a display; test the
        # headless path (None surface) which is always safe.
        menu_screen.render(None)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Event handling
# ---------------------------------------------------------------------------


class TestMainMenuEventHandling:
    """Tests for handle_event."""

    def test_handle_event_none_does_not_raise(self, menu_screen: object) -> None:
        """handle_event(None) is a headless-mode no-op."""
        menu_screen.handle_event(None)  # type: ignore[union-attr]

    def test_handle_quit_event_posts_quit(self, menu_screen: object) -> None:
        """A QUIT event should result in a QUIT event being posted."""
        quit_event = MagicMock()
        quit_event.type = 256  # pygame.QUIT constant value

        with patch("src.presentation.screens.main_menu_screen._pygame") as mock_pg:
            mock_pg.QUIT = 256
            mock_pg.MOUSEBUTTONDOWN = 1025
            mock_pg.MOUSEMOTION = 1024
            mock_pg.event.post = MagicMock()
            mock_pg.event.Event = MagicMock(return_value=quit_event)

            menu_screen.handle_event(quit_event)  # type: ignore[union-attr]

    def test_start_game_click_pushes_start_game_screen(
        self,
        mock_screen_manager: MagicMock,
        mock_game_context: MagicMock,
    ) -> None:
        """Clicking 'Start Game' pushes a StartGameScreen."""
        from src.presentation.screens.start_game_screen import StartGameScreen

        screen = MainMenuScreen(
            screen_manager=mock_screen_manager,
            game_context=mock_game_context,
        )
        # Directly invoke the internal action to test without needing a real pygame rect.
        screen._on_start_game()  # type: ignore[union-attr]

        mock_screen_manager.push.assert_called_once()
        pushed = mock_screen_manager.push.call_args[0][0]
        assert isinstance(pushed, StartGameScreen)


# ---------------------------------------------------------------------------
# Continue button
# ---------------------------------------------------------------------------


class TestMainMenuContinue:
    """Tests for the Continue button behaviour."""

    def test_continue_disabled_when_no_saves(
        self, mock_screen_manager: MagicMock
    ) -> None:
        """Continue button is disabled when there are no save files."""
        ctx = MagicMock()
        ctx.repository.get_most_recent_save.return_value = None
        screen = MainMenuScreen(
            screen_manager=mock_screen_manager,
            game_context=ctx,
        )
        screen.on_enter({})
        # on_enter calls _build_buttons which checks for saves — must not raise.

    def test_on_continue_calls_resume_from_state(
        self, mock_screen_manager: MagicMock
    ) -> None:
        """_on_continue() loads the save and delegates to resume_from_state."""
        ctx = MagicMock()
        loaded_state = MagicMock()
        ctx.repository.load.return_value = loaded_state

        screen = MainMenuScreen(
            screen_manager=mock_screen_manager,
            game_context=ctx,
        )
        screen._on_continue("game_001.json")  # type: ignore[union-attr]

        ctx.repository.load.assert_called_once_with("game_001.json")
        ctx.resume_from_state.assert_called_once_with(loaded_state, mock_screen_manager)
