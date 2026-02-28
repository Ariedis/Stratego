"""
test_task_popup_handover.py — Unit tests for 2-player local handover prompt
in the task popup.

Epic: EPIC-8 | User Story: US-809
Covers acceptance criteria: AC-1 through AC-4
Specification: ux-user-journeys-task-popup.md §Journey 5;
               ux-wireframe-task-popup.md §9 annotation 6
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.presentation.overlays.task_popup_overlay import (
        TaskPopupOverlay,  # type: ignore[import]
    )

    _OVERLAY_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    TaskPopupOverlay = None  # type: ignore[assignment, misc]
    _OVERLAY_AVAILABLE = False

try:
    from src.domain.army_mod import UnitTask  # type: ignore[attr-defined]

    _UNIT_TASK_AVAILABLE = True
except (ImportError, AttributeError):
    UnitTask = None  # type: ignore[assignment, misc]
    _UNIT_TASK_AVAILABLE = False

try:
    from src.domain.enums import PlayerSide

    _ENUMS_AVAILABLE = True
except ImportError:
    PlayerSide = None  # type: ignore[assignment, misc]
    _ENUMS_AVAILABLE = False

pytestmark = pytest.mark.xfail(
    not _OVERLAY_AVAILABLE,
    reason="TaskPopupOverlay not yet implemented in src.presentation.overlays",
    strict=False,
)

# Game mode constants — use strings if the enum/constant is not yet available.
try:
    from src.presentation.screens.start_game_screen import (
        GAME_MODE_TWO_PLAYER,
        GAME_MODE_VS_AI,
    )
except ImportError:
    GAME_MODE_TWO_PLAYER = "TWO_PLAYER"  # type: ignore[assignment]
    GAME_MODE_VS_AI = "VS_AI"  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def _make_overlay(
    game_mode: str,
    captured_side: object = None,
    capturing_side: object = None,
) -> object:
    """Create a TaskPopupOverlay with the given game_mode and captured player side."""
    if captured_side is None:
        captured_side = PlayerSide.RED
    if capturing_side is None:
        capturing_side = PlayerSide.BLUE
    task = UnitTask(description="Do 20 situps", image_path=None)  # type: ignore[misc]
    surface = MagicMock()
    surface.get_size.return_value = (1280, 720)
    return TaskPopupOverlay(  # type: ignore[misc]
        surface=surface,
        task=task,
        capturing_side=capturing_side,
        capturing_unit_name="Scout Rider",
        captured_unit_name="Miner",
        captured_player_side=captured_side,
        game_mode=game_mode,
    )


# ---------------------------------------------------------------------------
# US-809 AC-1: 2-player local mode — handover sub-line present
# ---------------------------------------------------------------------------


class TestHandoverSublineShown:
    """AC-1: In 2-player local mode, 'Pass the device to [colour] player' is shown."""

    def test_handover_subline_shown_in_two_player_mode(self) -> None:
        """AC-1: game_mode == TWO_PLAYER → show_handover_prompt is True."""
        overlay = _make_overlay(game_mode=GAME_MODE_TWO_PLAYER)
        assert overlay.show_handover_prompt is True  # type: ignore[union-attr]

    def test_handover_subline_text_is_correct_blue_captured(self) -> None:
        """AC-1: Captured player is Blue → sub-line reads 'Pass the device to Blue player'."""
        overlay = _make_overlay(
            game_mode=GAME_MODE_TWO_PLAYER,
            captured_side=PlayerSide.BLUE,
            capturing_side=PlayerSide.RED,
        )
        assert overlay.handover_prompt_text == "Pass the device to Blue player"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-809 AC-2: vs-AI mode — handover sub-line NOT shown
# ---------------------------------------------------------------------------


class TestHandoverSublineHiddenVsAi:
    """AC-2: In vs-AI mode, the 'Pass the device to…' sub-line must not appear."""

    def test_handover_subline_hidden_in_vs_ai_mode(self) -> None:
        """AC-2: game_mode == VS_AI → show_handover_prompt is False."""
        overlay = _make_overlay(game_mode=GAME_MODE_VS_AI)
        assert overlay.show_handover_prompt is False  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-809 AC-3: 2-player — Red player captured → pass to Red
# ---------------------------------------------------------------------------


class TestHandoverRedCaptured:
    """AC-3: Red team captured → sub-line reads 'Pass the device to Red player'."""

    def test_handover_text_for_red_captured(self) -> None:
        """AC-3: captured_player_side=RED → 'Pass the device to Red player'."""
        overlay = _make_overlay(
            game_mode=GAME_MODE_TWO_PLAYER,
            captured_side=PlayerSide.RED,
            capturing_side=PlayerSide.BLUE,
        )
        assert overlay.handover_prompt_text == "Pass the device to Red player"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-809 AC-4: 2-player — Blue player captured → pass to Blue
# ---------------------------------------------------------------------------


class TestHandoverBlueCaptured:
    """AC-4: Blue team captured → sub-line reads 'Pass the device to Blue player'."""

    def test_handover_text_for_blue_captured(self) -> None:
        """AC-4: captured_player_side=BLUE → 'Pass the device to Blue player'."""
        overlay = _make_overlay(
            game_mode=GAME_MODE_TWO_PLAYER,
            captured_side=PlayerSide.BLUE,
            capturing_side=PlayerSide.RED,
        )
        assert overlay.handover_prompt_text == "Pass the device to Blue player"  # type: ignore[union-attr]
