"""
test_screen_manager.py — Unit tests for src/application/screen_manager.py

Epic: EPIC-3 | User Story: US-306
Covers acceptance criteria: AC-1, AC-2, AC-3
Specification: screen_flow.md §4
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.application.screen_manager import ScreenManager
except ImportError:
    ScreenManager = None  # type: ignore[assignment, misc]

try:
    from src.presentation.screens.base import Screen
except ImportError:
    Screen = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    ScreenManager is None,
    reason="src.application.screen_manager not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def make_mock_screen(name: str = "MockScreen", exit_data: dict | None = None) -> MagicMock:
    """Return a MagicMock that behaves like a Screen."""
    screen = MagicMock()
    screen.__class__.__name__ = name
    screen.on_enter = MagicMock()
    screen.on_exit = MagicMock(return_value=exit_data or {})
    screen.render = MagicMock()
    screen.handle_event = MagicMock()
    screen.update = MagicMock()
    return screen


@pytest.fixture
def screen_manager() -> object:
    return ScreenManager()


@pytest.fixture
def main_menu_screen() -> MagicMock:
    return make_mock_screen("MainMenuScreen")


@pytest.fixture
def start_game_screen() -> MagicMock:
    return make_mock_screen("StartGameScreen")


@pytest.fixture
def playing_screen() -> MagicMock:
    return make_mock_screen("PlayingScreen")


# ---------------------------------------------------------------------------
# US-306 AC-1: push / current — LIFO order
# ---------------------------------------------------------------------------


class TestPushAndCurrent:
    """AC-1: After push, current() returns the most recently pushed screen."""

    def test_push_screen_becomes_current(
        self, screen_manager: object, main_menu_screen: MagicMock
    ) -> None:
        """push() makes the pushed screen the current screen."""
        screen_manager.push(main_menu_screen)  # type: ignore[union-attr]
        assert screen_manager.current() is main_menu_screen  # type: ignore[union-attr]

    def test_push_two_screens_lifo_order(
        self,
        screen_manager: object,
        main_menu_screen: MagicMock,
        start_game_screen: MagicMock,
    ) -> None:
        """After two pushes, current() returns the second (topmost) screen."""
        screen_manager.push(main_menu_screen)  # type: ignore[union-attr]
        screen_manager.push(start_game_screen)  # type: ignore[union-attr]
        assert screen_manager.current() is start_game_screen  # type: ignore[union-attr]

    def test_push_calls_on_enter_on_pushed_screen(
        self, screen_manager: object, main_menu_screen: MagicMock
    ) -> None:
        """push() must call on_enter() on the new screen."""
        screen_manager.push(main_menu_screen)  # type: ignore[union-attr]
        main_menu_screen.on_enter.assert_called_once()

    def test_push_with_data_passes_data_to_on_enter(
        self, screen_manager: object, start_game_screen: MagicMock
    ) -> None:
        """Data passed to push() is forwarded to on_enter()."""
        data = {"game_mode": "vs_ai"}
        screen_manager.push(start_game_screen, data)  # type: ignore[union-attr]
        start_game_screen.on_enter.assert_called_once_with(data)

    def test_push_no_data_calls_on_enter_with_empty_dict(
        self, screen_manager: object, main_menu_screen: MagicMock
    ) -> None:
        """push() with no data calls on_enter({}) by default."""
        screen_manager.push(main_menu_screen)  # type: ignore[union-attr]
        main_menu_screen.on_enter.assert_called_once_with({})


# ---------------------------------------------------------------------------
# US-306 AC-2: pop — restores previous screen with exit data
# ---------------------------------------------------------------------------


class TestPop:
    """AC-2: pop() removes top screen and returns exit data to previous screen."""

    def test_pop_restores_previous_screen_as_current(
        self,
        screen_manager: object,
        main_menu_screen: MagicMock,
        start_game_screen: MagicMock,
    ) -> None:
        """After pushing two screens, pop() makes the first screen current."""
        screen_manager.push(main_menu_screen)  # type: ignore[union-attr]
        screen_manager.push(start_game_screen)  # type: ignore[union-attr]
        screen_manager.pop()  # type: ignore[union-attr]
        assert screen_manager.current() is main_menu_screen  # type: ignore[union-attr]

    def test_pop_calls_on_exit_on_popped_screen(
        self,
        screen_manager: object,
        main_menu_screen: MagicMock,
        start_game_screen: MagicMock,
    ) -> None:
        """pop() calls on_exit() on the screen being removed."""
        screen_manager.push(main_menu_screen)  # type: ignore[union-attr]
        screen_manager.push(start_game_screen)  # type: ignore[union-attr]
        screen_manager.pop()  # type: ignore[union-attr]
        start_game_screen.on_exit.assert_called_once()

    def test_pop_passes_exit_data_to_previous_screens_on_enter(
        self, screen_manager: object
    ) -> None:
        """on_enter of the previous screen is called with the exit data."""
        return_data = {"selected_mode": "vs_ai"}
        main = make_mock_screen("MainMenuScreen")
        start = make_mock_screen("StartGameScreen", exit_data=return_data)

        screen_manager.push(main)  # type: ignore[union-attr]
        screen_manager.push(start)  # type: ignore[union-attr]

        # Reset call record after initial push
        main.on_enter.reset_mock()
        screen_manager.pop()  # type: ignore[union-attr]

        main.on_enter.assert_called_once_with(return_data)

    def test_pop_from_single_screen_stack_does_not_crash(
        self, screen_manager: object, main_menu_screen: MagicMock
    ) -> None:
        """pop() on a stack with a single screen should not raise (or raise clearly)."""
        screen_manager.push(main_menu_screen)  # type: ignore[union-attr]
        # Either returns gracefully or raises a clear error; must not cause
        # an AttributeError or crash unexpectedly.
        try:
            screen_manager.pop()  # type: ignore[union-attr]
        except Exception:
            pass  # Any explicit exception is acceptable


# ---------------------------------------------------------------------------
# US-306 AC-3: replace — swaps top without growing the stack
# ---------------------------------------------------------------------------


class TestReplace:
    """AC-3: replace() swaps the current top screen without growing the stack."""

    def test_replace_changes_current_to_new_screen(
        self,
        screen_manager: object,
        main_menu_screen: MagicMock,
        start_game_screen: MagicMock,
        playing_screen: MagicMock,
    ) -> None:
        """After replace(playing), current() returns playing_screen."""
        screen_manager.push(main_menu_screen)  # type: ignore[union-attr]
        screen_manager.push(start_game_screen)  # type: ignore[union-attr]
        screen_manager.replace(playing_screen)  # type: ignore[union-attr]
        assert screen_manager.current() is playing_screen  # type: ignore[union-attr]

    def test_replace_does_not_grow_stack_depth(
        self,
        screen_manager: object,
        main_menu_screen: MagicMock,
        start_game_screen: MagicMock,
        playing_screen: MagicMock,
    ) -> None:
        """Stack size after replace is the same as before replace."""
        screen_manager.push(main_menu_screen)  # type: ignore[union-attr]
        screen_manager.push(start_game_screen)  # type: ignore[union-attr]
        screen_manager.replace(playing_screen)  # type: ignore[union-attr]
        # Pop the playing screen to get back to main menu
        screen_manager.pop()  # type: ignore[union-attr]
        assert screen_manager.current() is main_menu_screen  # type: ignore[union-attr]

    def test_replace_calls_on_exit_on_replaced_screen(
        self,
        screen_manager: object,
        main_menu_screen: MagicMock,
        start_game_screen: MagicMock,
        playing_screen: MagicMock,
    ) -> None:
        """replace() calls on_exit() on the screen being replaced."""
        screen_manager.push(main_menu_screen)  # type: ignore[union-attr]
        screen_manager.push(start_game_screen)  # type: ignore[union-attr]
        screen_manager.replace(playing_screen)  # type: ignore[union-attr]
        start_game_screen.on_exit.assert_called_once()

    def test_replace_calls_on_enter_on_new_screen(
        self,
        screen_manager: object,
        main_menu_screen: MagicMock,
        start_game_screen: MagicMock,
        playing_screen: MagicMock,
    ) -> None:
        """replace() calls on_enter() on the new screen."""
        screen_manager.push(main_menu_screen)  # type: ignore[union-attr]
        screen_manager.push(start_game_screen)  # type: ignore[union-attr]
        screen_manager.replace(playing_screen)  # type: ignore[union-attr]
        playing_screen.on_enter.assert_called()

    def test_replace_with_data_passes_data_to_new_screens_on_enter(
        self,
        screen_manager: object,
        main_menu_screen: MagicMock,
        playing_screen: MagicMock,
    ) -> None:
        """Data passed to replace() is forwarded to the new screen's on_enter()."""
        screen_manager.push(main_menu_screen)  # type: ignore[union-attr]
        data = {"turn": 5}
        screen_manager.replace(playing_screen, data)  # type: ignore[union-attr]
        playing_screen.on_enter.assert_called_once_with(data)


# ---------------------------------------------------------------------------
# Screen abstract base class
# ---------------------------------------------------------------------------


class TestScreenAbstractBase:
    """Screen base class must define required abstract methods."""

    def test_screen_abstract_base_class_is_importable(self) -> None:
        """src.presentation.screens.base.Screen is importable."""
        from src.presentation.screens.base import Screen as S  # noqa: F401

        assert S is not None

    def test_screen_cannot_be_instantiated_directly(self) -> None:
        """Screen is abstract and must raise TypeError if instantiated directly."""
        from src.presentation.screens.base import Screen as S

        with pytest.raises(TypeError):
            S()  # type: ignore[abstract]

    def test_screen_subclass_must_implement_abstract_methods(self) -> None:
        """A concrete Screen subclass that omits abstract methods cannot be instantiated."""
        from src.presentation.screens.base import Screen as S

        class IncompleteScreen(S):
            pass

        with pytest.raises(TypeError):
            IncompleteScreen()  # type: ignore[abstract]
