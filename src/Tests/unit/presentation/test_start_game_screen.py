"""
test_start_game_screen.py — Unit tests for StartGameScreen.

Epic: EPIC-4 | User Story: US-409
Covers: on_enter, on_exit, game mode selection, AI difficulty selection,
        navigation (confirm / back).
Specification: screen_flow.md §3.2
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.domain.enums import PlayerType

try:
    from src.presentation.screens.start_game_screen import (
        GAME_MODE_TWO_PLAYER,
        GAME_MODE_VS_AI,
        StartGameScreen,
    )
except ImportError:
    StartGameScreen = None  # type: ignore[assignment, misc]
    GAME_MODE_TWO_PLAYER = "TWO_PLAYER"  # type: ignore[assignment]
    GAME_MODE_VS_AI = "VS_AI"  # type: ignore[assignment]

pytestmark = pytest.mark.xfail(
    StartGameScreen is None,
    reason="StartGameScreen not implemented yet",
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
def mock_game_context() -> MagicMock:
    ctx = MagicMock()
    ctx.start_new_game = MagicMock()
    return ctx


@pytest.fixture
def start_screen(
    mock_screen_manager: MagicMock, mock_game_context: MagicMock
) -> object:
    screen = StartGameScreen(
        screen_manager=mock_screen_manager,
        game_context=mock_game_context,
    )
    screen.on_enter({})
    return screen


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestStartGameLifecycle:
    """Tests for on_enter / on_exit."""

    def test_on_enter_does_not_raise(
        self, mock_screen_manager: MagicMock, mock_game_context: MagicMock
    ) -> None:
        screen = StartGameScreen(
            screen_manager=mock_screen_manager,
            game_context=mock_game_context,
        )
        screen.on_enter({})

    def test_on_exit_returns_game_mode(self, start_screen: object) -> None:
        result = start_screen.on_exit()  # type: ignore[union-attr]
        assert "game_mode" in result

    def test_on_exit_returns_ai_difficulty(self, start_screen: object) -> None:
        result = start_screen.on_exit()  # type: ignore[union-attr]
        assert "ai_difficulty" in result

    def test_default_game_mode_is_two_player(self, start_screen: object) -> None:
        assert start_screen.game_mode == GAME_MODE_TWO_PLAYER  # type: ignore[union-attr]

    def test_default_ai_difficulty_is_medium(self, start_screen: object) -> None:
        assert start_screen.ai_difficulty == PlayerType.AI_MEDIUM  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Mode selection
# ---------------------------------------------------------------------------


class TestModeSelection:
    """Tests for two-player / vs-AI mode toggling."""

    def test_select_vs_ai_changes_mode(self, start_screen: object) -> None:
        start_screen._select_vs_ai()  # type: ignore[union-attr]
        assert start_screen.game_mode == GAME_MODE_VS_AI  # type: ignore[union-attr]

    def test_select_two_player_changes_mode(self, start_screen: object) -> None:
        start_screen._select_vs_ai()  # type: ignore[union-attr]
        start_screen._select_two_player()  # type: ignore[union-attr]
        assert start_screen.game_mode == GAME_MODE_TWO_PLAYER  # type: ignore[union-attr]

    def test_select_easy_difficulty(self, start_screen: object) -> None:
        start_screen._select_vs_ai()  # type: ignore[union-attr]
        start_screen._make_difficulty_selector(PlayerType.AI_EASY)()  # type: ignore[union-attr]
        assert start_screen.ai_difficulty == PlayerType.AI_EASY  # type: ignore[union-attr]

    def test_select_hard_difficulty(self, start_screen: object) -> None:
        start_screen._select_vs_ai()  # type: ignore[union-attr]
        start_screen._make_difficulty_selector(PlayerType.AI_HARD)()  # type: ignore[union-attr]
        assert start_screen.ai_difficulty == PlayerType.AI_HARD  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------


class TestStartGameNavigation:
    """Tests for Confirm and Back navigation."""

    def test_back_pops_screen_manager(
        self,
        start_screen: object,
        mock_screen_manager: MagicMock,
    ) -> None:
        """Clicking Back calls screen_manager.pop()."""
        start_screen._on_back()  # type: ignore[union-attr]
        mock_screen_manager.pop.assert_called_once()

    def test_confirm_two_player_calls_start_new_game(
        self,
        start_screen: object,
        mock_game_context: MagicMock,
        mock_screen_manager: MagicMock,
    ) -> None:
        """Confirm in two-player mode calls game_context.start_new_game."""
        start_screen._select_two_player()  # type: ignore[union-attr]
        start_screen._on_confirm()  # type: ignore[union-attr]
        mock_game_context.start_new_game.assert_called_once_with(
            game_mode=GAME_MODE_TWO_PLAYER,
            ai_difficulty=None,
            screen_manager=mock_screen_manager,
        )

    def test_confirm_vs_ai_passes_difficulty(
        self,
        start_screen: object,
        mock_game_context: MagicMock,
        mock_screen_manager: MagicMock,
    ) -> None:
        """Confirm in vs-AI mode passes the selected difficulty."""
        start_screen._select_vs_ai()  # type: ignore[union-attr]
        start_screen._make_difficulty_selector(PlayerType.AI_EASY)()  # type: ignore[union-attr]
        start_screen._on_confirm()  # type: ignore[union-attr]
        mock_game_context.start_new_game.assert_called_once_with(
            game_mode=GAME_MODE_VS_AI,
            ai_difficulty=PlayerType.AI_EASY,
            screen_manager=mock_screen_manager,
        )

    def test_update_does_not_raise(self, start_screen: object) -> None:
        start_screen.update(0.016)  # type: ignore[union-attr]

    def test_render_with_none_does_not_raise(self, start_screen: object) -> None:
        start_screen.render(None)  # type: ignore[union-attr]

    def test_handle_event_none_does_not_raise(self, start_screen: object) -> None:
        start_screen.handle_event(None)  # type: ignore[union-attr]
