"""
test_task_popup_input.py — Unit tests for TaskPopupOverlay input blocking
and keyboard navigation.

Epic: EPIC-8 | User Story: US-805
Covers acceptance criteria: AC-1 through AC-4 (input blocking),
                             AC-7 through AC-9 (keyboard navigation)
Specification: ux-wireframe-task-popup.md §4.1–§4.4, §11;
               ux-user-journeys-task-popup.md §Journey 4; ux-accessibility.md
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.presentation.overlays.task_popup_overlay import TaskPopupOverlay  # type: ignore[import]

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

# ---------------------------------------------------------------------------
# Synthetic pygame event type constants (pygame may not be installed)
# ---------------------------------------------------------------------------

try:
    import pygame as _pg

    _MOUSEBUTTONDOWN = _pg.MOUSEBUTTONDOWN
    _KEYDOWN = _pg.KEYDOWN
    _K_ESCAPE = _pg.K_ESCAPE
    _K_s = _pg.K_s
    _K_u = _pg.K_u
    _K_q = _pg.K_q
    _K_TAB = _pg.K_TAB
    _K_RETURN = _pg.K_RETURN
    _K_SPACE = _pg.K_SPACE
    _K_UP = _pg.K_UP
except (ImportError, AttributeError):
    _MOUSEBUTTONDOWN = 1025
    _KEYDOWN = 768
    _K_ESCAPE = 27
    _K_s = 115
    _K_u = 117
    _K_q = 113
    _K_TAB = 9
    _K_RETURN = 13
    _K_SPACE = 32
    _K_UP = 273


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def _make_overlay() -> object:
    """Create a TaskPopupOverlay with a headless mock surface."""
    task = UnitTask(description="Do 20 situps", image_path=None)  # type: ignore[misc]
    surface = MagicMock()
    surface.get_size.return_value = (1280, 720)
    return TaskPopupOverlay(  # type: ignore[misc]
        surface=surface,
        task=task,
        capturing_side=PlayerSide.BLUE,
        capturing_unit_name="Scout Rider",
        captured_unit_name="Miner",
    )


def _make_event(event_type: int, **attrs: object) -> MagicMock:
    """Create a minimal mock pygame event."""
    evt = MagicMock()
    evt.type = event_type
    for key, value in attrs.items():
        setattr(evt, key, value)
    return evt


def _make_rect(x: int, y: int, w: int, h: int) -> MagicMock:
    rect = MagicMock()
    rect.collidepoint = lambda pos: (
        x <= pos[0] < x + w and y <= pos[1] < y + h
    )
    return rect


# ---------------------------------------------------------------------------
# US-805 AC-1: Board clicks suppressed while popup is visible
# ---------------------------------------------------------------------------


class TestBoardClickSuppressed:
    """AC-1: Board cell clicks must not trigger piece selection or moves."""

    def test_board_click_is_consumed(self) -> None:
        """AC-1: handle_event returns True (consumed) for a board click."""
        overlay = _make_overlay()
        board_click = _make_event(_MOUSEBUTTONDOWN, button=1, pos=(100, 400))
        result = overlay.handle_event(board_click)  # type: ignore[union-attr]
        assert result is True

    def test_board_click_does_not_dismiss_popup(self) -> None:
        """AC-1: Clicking outside the modal card does not dismiss the popup."""
        overlay = _make_overlay()
        # Click far outside the card (top-left corner)
        outside_click = _make_event(_MOUSEBUTTONDOWN, button=1, pos=(10, 10))
        overlay.handle_event(outside_click)  # type: ignore[union-attr]
        assert overlay.is_visible is True  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-805 AC-2: Key presses (S, U, Q, arrow) suppressed while popup is visible
# ---------------------------------------------------------------------------


class TestKeysSuppressed:
    """AC-2: S, U, Q, and arrow keys are suppressed while popup is visible."""

    @pytest.mark.parametrize(
        "key",
        [_K_s, _K_u, _K_q, _K_UP],
        ids=["save_s", "undo_u", "quit_q", "arrow_up"],
    )
    def test_key_is_consumed(self, key: int) -> None:
        """AC-2: handle_event returns True (consumed) for suppressed keys."""
        overlay = _make_overlay()
        evt = _make_event(_KEYDOWN, key=key)
        result = overlay.handle_event(evt)  # type: ignore[union-attr]
        assert result is True

    @pytest.mark.parametrize(
        "key",
        [_K_s, _K_u, _K_q, _K_UP],
        ids=["save_s", "undo_u", "quit_q", "arrow_up"],
    )
    def test_key_does_not_dismiss_popup(self, key: int) -> None:
        """AC-2: Pressing suppressed keys does not dismiss the popup."""
        overlay = _make_overlay()
        evt = _make_event(_KEYDOWN, key=key)
        overlay.handle_event(evt)  # type: ignore[union-attr]
        assert overlay.is_visible is True  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-805 AC-3: Click outside modal card does not dismiss popup
# ---------------------------------------------------------------------------


class TestOutsideClickDoesNotDismiss:
    """AC-3: Clicking outside the card must not dismiss the popup."""

    def test_outside_click_popup_stays_visible(self) -> None:
        """AC-3: Click at (0, 0) — outside any 720×380 card — keeps popup visible."""
        overlay = _make_overlay()
        outside_click = _make_event(_MOUSEBUTTONDOWN, button=1, pos=(0, 0))
        overlay.handle_event(outside_click)  # type: ignore[union-attr]
        assert overlay.is_visible is True  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-805 AC-4: Escape key does not dismiss popup
# ---------------------------------------------------------------------------


class TestEscapeDoesNotDismiss:
    """AC-4: Pressing Escape while popup is visible must not dismiss it."""

    def test_escape_key_does_not_dismiss(self) -> None:
        """AC-4: Escape key → popup remains visible."""
        overlay = _make_overlay()
        escape_evt = _make_event(_KEYDOWN, key=_K_ESCAPE)
        overlay.handle_event(escape_evt)  # type: ignore[union-attr]
        assert overlay.is_visible is True  # type: ignore[union-attr]

    def test_escape_key_is_consumed(self) -> None:
        """AC-4: handle_event returns True (consumed) for Escape key."""
        overlay = _make_overlay()
        escape_evt = _make_event(_KEYDOWN, key=_K_ESCAPE)
        result = overlay.handle_event(escape_evt)  # type: ignore[union-attr]
        assert result is True


# ---------------------------------------------------------------------------
# US-805 AC-7: Complete button auto-focused on popup open
# ---------------------------------------------------------------------------


class TestButtonAutoFocus:
    """AC-7: 'Complete ✓' button is auto-focused when popup opens."""

    def test_button_focused_on_creation(self) -> None:
        """AC-7: button_focused == True immediately after construction."""
        overlay = _make_overlay()
        assert overlay.button_focused is True  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-805 AC-8: Tab key moves focus to Complete button
# ---------------------------------------------------------------------------


class TestTabFocusNavigation:
    """AC-8: Tab moves focus to the 'Complete ✓' button."""

    def test_tab_sets_button_focused(self) -> None:
        """AC-8: Pressing Tab → button_focused becomes True."""
        overlay = _make_overlay()
        # Unfocus manually to ensure tab re-focuses
        object.__setattr__(overlay, "button_focused", False) if hasattr(
            overlay, "__dataclass_fields__"
        ) else setattr(overlay, "_button_focused", False)
        tab_evt = _make_event(_KEYDOWN, key=_K_TAB)
        overlay.handle_event(tab_evt)  # type: ignore[union-attr]
        assert overlay.button_focused is True  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-805 AC-9: Enter / Space when button is focused dismisses the popup
# ---------------------------------------------------------------------------


class TestEnterSpaceDismissesPopup:
    """AC-9: Enter or Space while button is focused dismisses the popup."""

    @pytest.mark.parametrize(
        "key,key_id",
        [(_K_RETURN, "enter"), (_K_SPACE, "space")],
        ids=["enter", "space"],
    )
    def test_key_dismisses_popup_when_button_focused(self, key: int, key_id: str) -> None:
        """AC-9: Enter/Space with button focused → popup dismissed (is_visible False)."""
        overlay = _make_overlay()
        assert overlay.button_focused is True  # pre-condition: button is focused  # type: ignore[union-attr]
        key_evt = _make_event(_KEYDOWN, key=key)
        overlay.handle_event(key_evt)  # type: ignore[union-attr]
        assert overlay.is_visible is False  # type: ignore[union-attr]
