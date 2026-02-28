"""
test_load_game_screen.py — Unit tests for LoadGameScreen.

Epic: EPIC-4 | User Story: US-411
Covers: on_enter, on_exit, save list loading, navigation (back).
Specification: screen_flow.md §3.4; ux-wireframe-load-game.md
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

try:
    from src.presentation.screens.load_game_screen import LoadGameScreen
except ImportError:
    LoadGameScreen = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    LoadGameScreen is None,
    reason="LoadGameScreen not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_screen_manager() -> MagicMock:
    sm = MagicMock()
    sm.push = MagicMock()
    sm.pop = MagicMock()
    sm.replace = MagicMock()
    return sm


@pytest.fixture
def mock_game_context_no_saves() -> MagicMock:
    """Game context with an empty save repository."""
    ctx = MagicMock()
    ctx.repository.list_saves.return_value = []
    return ctx


@pytest.fixture
def mock_game_context_with_saves() -> MagicMock:
    """Game context with two save entries."""
    ctx = MagicMock()
    ctx.repository.list_saves.return_value = ["save1.json", "save2.json"]
    return ctx


@pytest.fixture
def load_screen_empty(
    mock_screen_manager: MagicMock, mock_game_context_no_saves: MagicMock
) -> object:
    screen = LoadGameScreen(
        screen_manager=mock_screen_manager,
        game_context=mock_game_context_no_saves,
    )
    screen.on_enter({})
    return screen


@pytest.fixture
def load_screen_with_saves(
    mock_screen_manager: MagicMock, mock_game_context_with_saves: MagicMock
) -> object:
    screen = LoadGameScreen(
        screen_manager=mock_screen_manager,
        game_context=mock_game_context_with_saves,
    )
    screen.on_enter({})
    return screen


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestLoadGameLifecycle:
    """Tests for on_enter / on_exit."""

    def test_on_enter_does_not_raise(
        self, mock_screen_manager: MagicMock, mock_game_context_no_saves: MagicMock
    ) -> None:
        screen = LoadGameScreen(
            screen_manager=mock_screen_manager,
            game_context=mock_game_context_no_saves,
        )
        screen.on_enter({})

    def test_on_exit_returns_empty_dict(self, load_screen_empty: object) -> None:
        assert load_screen_empty.on_exit() == {}  # type: ignore[union-attr]

    def test_on_enter_loads_saves_list(self, load_screen_with_saves: object) -> None:
        assert len(load_screen_with_saves.saves) == 2  # type: ignore[union-attr]

    def test_on_enter_empty_saves_list(self, load_screen_empty: object) -> None:
        assert load_screen_empty.saves == []  # type: ignore[union-attr]

    def test_selected_index_defaults_to_minus_one(
        self, load_screen_empty: object
    ) -> None:
        assert load_screen_empty.selected_index == -1  # type: ignore[union-attr]

    def test_update_does_not_raise(self, load_screen_empty: object) -> None:
        load_screen_empty.update(0.016)  # type: ignore[union-attr]

    def test_render_with_none_does_not_raise(self, load_screen_empty: object) -> None:
        load_screen_empty.render(None)  # type: ignore[union-attr]

    def test_handle_event_none_does_not_raise(self, load_screen_empty: object) -> None:
        load_screen_empty.handle_event(None)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------


class TestLoadGameNavigation:
    """Tests for Back navigation."""

    def test_back_pops_screen_manager(
        self, load_screen_empty: object, mock_screen_manager: MagicMock
    ) -> None:
        load_screen_empty._on_back()  # type: ignore[union-attr]
        mock_screen_manager.pop.assert_called_once()


# ---------------------------------------------------------------------------
# Load action
# ---------------------------------------------------------------------------


class TestLoadGameLoadAction:
    """Tests for the Load action."""

    def test_on_load_calls_resume_from_state(
        self, mock_screen_manager: MagicMock
    ) -> None:
        """_on_load() loads the selected save and delegates to resume_from_state."""
        ctx = MagicMock()
        loaded_state = MagicMock()
        ctx.repository.list_saves.return_value = ["save1.json"]
        ctx.repository.load.return_value = loaded_state

        screen = LoadGameScreen(
            screen_manager=mock_screen_manager,
            game_context=ctx,
        )
        screen.on_enter({})
        screen._selected_index = 0  # type: ignore[union-attr]
        screen._on_load()  # type: ignore[union-attr]

        ctx.repository.load.assert_called_once_with("save1.json")
        ctx.resume_from_state.assert_called_once_with(loaded_state, mock_screen_manager)

    def test_on_load_does_nothing_when_no_selection(
        self, load_screen_with_saves: object
    ) -> None:
        """_on_load() is a no-op when selected_index is -1."""
        ctx = load_screen_with_saves._game_context  # type: ignore[union-attr]
        load_screen_with_saves._on_load()  # type: ignore[union-attr]
        ctx.repository.load.assert_not_called()
