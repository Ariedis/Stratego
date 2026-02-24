"""
test_settings_screen.py — Unit tests for SettingsScreen.

Epic: EPIC-4 | User Story: US-412
Covers: on_enter, on_exit, reset, navigation.
Specification: screen_flow.md §3.5; ux-wireframe-settings.md
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

try:
    from src.presentation.screens.settings_screen import (
        SettingsScreen,
        _DEFAULT_FPS_CAP,
        _DEFAULT_FULLSCREEN,
        _DEFAULT_MUSIC_ENABLED,
        _DEFAULT_SFX_ENABLED,
        _DEFAULT_UNDO_ENABLED,
    )
except ImportError:
    SettingsScreen = None  # type: ignore[assignment, misc]
    _DEFAULT_FPS_CAP = 60  # type: ignore[assignment]
    _DEFAULT_FULLSCREEN = False  # type: ignore[assignment]
    _DEFAULT_MUSIC_ENABLED = True  # type: ignore[assignment]
    _DEFAULT_SFX_ENABLED = True  # type: ignore[assignment]
    _DEFAULT_UNDO_ENABLED = False  # type: ignore[assignment]

pytestmark = pytest.mark.xfail(
    SettingsScreen is None,
    reason="SettingsScreen not implemented yet",
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
    # Simulate a config with display attributes
    ctx.config.display.fullscreen = False
    ctx.config.display.fps_cap = 60
    # Game settings attributes — explicitly set to avoid MagicMock interference
    ctx.config.undo_enabled = False
    ctx.config.sfx_enabled = True
    ctx.config.sfx_volume = 75
    ctx.config.music_enabled = True
    ctx.config.music_volume = 50
    ctx.config.reduce_motion = False
    ctx.config.colour_blind = False
    return ctx


@pytest.fixture
def settings_screen(
    mock_screen_manager: MagicMock, mock_game_context: MagicMock
) -> object:
    screen = SettingsScreen(
        screen_manager=mock_screen_manager,
        game_context=mock_game_context,
    )
    screen.on_enter({})
    return screen


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestSettingsLifecycle:
    """Tests for on_enter / on_exit."""

    def test_on_enter_does_not_raise(
        self, mock_screen_manager: MagicMock, mock_game_context: MagicMock
    ) -> None:
        screen = SettingsScreen(
            screen_manager=mock_screen_manager,
            game_context=mock_game_context,
        )
        screen.on_enter({})

    def test_on_exit_returns_empty_dict(self, settings_screen: object) -> None:
        assert settings_screen.on_exit() == {}  # type: ignore[union-attr]

    def test_update_does_not_raise(self, settings_screen: object) -> None:
        settings_screen.update(0.016)  # type: ignore[union-attr]

    def test_render_with_none_does_not_raise(self, settings_screen: object) -> None:
        settings_screen.render(None)  # type: ignore[union-attr]

    def test_handle_event_none_does_not_raise(self, settings_screen: object) -> None:
        settings_screen.handle_event(None)  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------


class TestSettingsDefaults:
    """Tests for default setting values."""

    def test_default_fullscreen_is_false(self, settings_screen: object) -> None:
        assert settings_screen.fullscreen == _DEFAULT_FULLSCREEN  # type: ignore[union-attr]

    def test_default_fps_cap(self, settings_screen: object) -> None:
        assert settings_screen.fps_cap == _DEFAULT_FPS_CAP  # type: ignore[union-attr]

    def test_default_undo_is_disabled(self, settings_screen: object) -> None:
        assert settings_screen.undo_enabled == _DEFAULT_UNDO_ENABLED  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


class TestSettingsReset:
    """Tests for the reset-to-defaults action."""

    def test_reset_restores_fullscreen_default(
        self, settings_screen: object
    ) -> None:
        settings_screen._fullscreen = True  # type: ignore[union-attr]
        settings_screen._on_reset()  # type: ignore[union-attr]
        assert settings_screen.fullscreen == _DEFAULT_FULLSCREEN  # type: ignore[union-attr]

    def test_reset_restores_fps_default(self, settings_screen: object) -> None:
        settings_screen._fps_cap = 999  # type: ignore[union-attr]
        settings_screen._on_reset()  # type: ignore[union-attr]
        assert settings_screen.fps_cap == _DEFAULT_FPS_CAP  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------


class TestSettingsNavigation:
    """Tests for Back navigation."""

    def test_back_pops_screen_manager(
        self, settings_screen: object, mock_screen_manager: MagicMock
    ) -> None:
        settings_screen._on_back()  # type: ignore[union-attr]
        mock_screen_manager.pop.assert_called_once()

    def test_apply_pops_screen_manager(
        self, settings_screen: object, mock_screen_manager: MagicMock
    ) -> None:
        settings_screen._on_apply()  # type: ignore[union-attr]
        mock_screen_manager.pop.assert_called_once()
