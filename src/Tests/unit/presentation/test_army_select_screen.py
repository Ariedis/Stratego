"""
test_army_select_screen.py — Unit tests for ArmySelectScreen.

Epic: EPIC-4 | User Story: US-410
Covers: on_enter, on_exit, navigation (confirm / back), army selection.
Specification: screen_flow.md §3.3; ux-wireframe-army-select.md
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.domain.enums import PlayerType

try:
    from src.presentation.screens.army_select_screen import ArmySelectScreen
    from src.presentation.screens.start_game_screen import (
        GAME_MODE_TWO_PLAYER,
        GAME_MODE_VS_AI,
    )
except ImportError:
    ArmySelectScreen = None  # type: ignore[assignment, misc]
    GAME_MODE_TWO_PLAYER = "TWO_PLAYER"  # type: ignore[assignment]
    GAME_MODE_VS_AI = "VS_AI"  # type: ignore[assignment]

pytestmark = pytest.mark.xfail(
    ArmySelectScreen is None,
    reason="ArmySelectScreen not implemented yet",
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
def army_screen_vs_ai(
    mock_screen_manager: MagicMock, mock_game_context: MagicMock
) -> object:
    """ArmySelectScreen in VS_AI mode."""
    screen = ArmySelectScreen(
        screen_manager=mock_screen_manager,
        game_context=mock_game_context,
        game_mode=GAME_MODE_VS_AI,
        ai_difficulty=PlayerType.AI_MEDIUM,
    )
    screen.on_enter({})
    return screen


@pytest.fixture
def army_screen_two_player(
    mock_screen_manager: MagicMock, mock_game_context: MagicMock
) -> object:
    """ArmySelectScreen in TWO_PLAYER mode."""
    screen = ArmySelectScreen(
        screen_manager=mock_screen_manager,
        game_context=mock_game_context,
        game_mode=GAME_MODE_TWO_PLAYER,
        ai_difficulty=None,
    )
    screen.on_enter({})
    return screen


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestArmySelectLifecycle:
    """Tests for on_enter / on_exit."""

    def test_on_enter_does_not_raise(
        self, mock_screen_manager: MagicMock, mock_game_context: MagicMock
    ) -> None:
        screen = ArmySelectScreen(
            screen_manager=mock_screen_manager,
            game_context=mock_game_context,
            game_mode=GAME_MODE_VS_AI,
        )
        screen.on_enter({})

    def test_on_exit_returns_game_mode(self, army_screen_vs_ai: object) -> None:
        result = army_screen_vs_ai.on_exit()  # type: ignore[union-attr]
        assert "game_mode" in result

    def test_on_exit_returns_ai_difficulty(self, army_screen_vs_ai: object) -> None:
        result = army_screen_vs_ai.on_exit()  # type: ignore[union-attr]
        assert "ai_difficulty" in result

    def test_on_exit_returns_player_armies(self, army_screen_vs_ai: object) -> None:
        result = army_screen_vs_ai.on_exit()  # type: ignore[union-attr]
        assert "player1_army" in result
        assert "player2_army" in result

    def test_update_does_not_raise(self, army_screen_vs_ai: object) -> None:
        army_screen_vs_ai.update(0.016)  # type: ignore[union-attr]

    def test_render_with_none_does_not_raise(self, army_screen_vs_ai: object) -> None:
        army_screen_vs_ai.render(None)  # type: ignore[union-attr]

    def test_handle_event_none_does_not_raise(self, army_screen_vs_ai: object) -> None:
        army_screen_vs_ai.handle_event(None)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------


class TestArmySelectNavigation:
    """Tests for Back and Confirm navigation."""

    def test_back_pops_screen_manager(
        self, army_screen_vs_ai: object, mock_screen_manager: MagicMock
    ) -> None:
        """Back calls screen_manager.pop()."""
        army_screen_vs_ai._on_back()  # type: ignore[union-attr]
        mock_screen_manager.pop.assert_called_once()

    def test_confirm_calls_start_new_game(
        self,
        army_screen_vs_ai: object,
        mock_game_context: MagicMock,
        mock_screen_manager: MagicMock,
    ) -> None:
        """Confirm delegates to game_context.start_new_game."""
        army_screen_vs_ai._on_confirm()  # type: ignore[union-attr]
        mock_game_context.start_new_game.assert_called_once()

    def test_confirm_vs_ai_passes_difficulty(
        self,
        army_screen_vs_ai: object,
        mock_game_context: MagicMock,
        mock_screen_manager: MagicMock,
    ) -> None:
        """Confirm in VS_AI mode passes the ai_difficulty to start_new_game."""
        army_screen_vs_ai._on_confirm()  # type: ignore[union-attr]
        call_kwargs = mock_game_context.start_new_game.call_args
        all_args = list(call_kwargs.args) + list(call_kwargs.kwargs.values())
        assert PlayerType.AI_MEDIUM in all_args

    def test_confirm_two_player_passes_none_difficulty(
        self,
        army_screen_two_player: object,
        mock_game_context: MagicMock,
    ) -> None:
        """Confirm in TWO_PLAYER mode passes ai_difficulty=None."""
        army_screen_two_player._on_confirm()  # type: ignore[union-attr]
        call_kwargs = mock_game_context.start_new_game.call_args
        all_args = list(call_kwargs.args) + list(call_kwargs.kwargs.values())
        assert None in all_args


# ---------------------------------------------------------------------------
# Army accessors
# ---------------------------------------------------------------------------


class TestArmySelectArmies:
    """Tests for default army selection."""

    def test_default_player1_army_is_classic(
        self, army_screen_vs_ai: object
    ) -> None:
        """Player 1 defaults to Classic Army."""
        assert army_screen_vs_ai.player1_army == "Classic Army"  # type: ignore[union-attr]

    def test_default_player2_army_is_classic(
        self, army_screen_vs_ai: object
    ) -> None:
        """Player 2 defaults to Classic Army."""
        assert army_screen_vs_ai.player2_army == "Classic Army"  # type: ignore[union-attr]
