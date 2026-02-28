"""
test_task_popup_overlay.py — Unit tests for TaskPopupOverlay visual layout.

Epic: EPIC-8 | User Story: US-803
Covers acceptance criteria: AC-1 through AC-7
Specification: ux-wireframe-task-popup.md §2, §3, §5, §6; screen_flow.md §3.7
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
    from src.domain.enums import PlayerSide, Rank

    _ENUMS_AVAILABLE = True
except ImportError:
    PlayerSide = None  # type: ignore[assignment, misc]
    Rank = None  # type: ignore[assignment, misc]
    _ENUMS_AVAILABLE = False

pytestmark = pytest.mark.xfail(
    not _OVERLAY_AVAILABLE,
    reason="TaskPopupOverlay not yet implemented in src.presentation.overlays",
    strict=False,
)

# ---------------------------------------------------------------------------
# Colour / layout constants from the wireframe (US-803 acceptance criteria)
# ---------------------------------------------------------------------------

_COLOUR_SURFACE = (40, 58, 88)         # COLOUR_SURFACE #283A58
_COLOUR_PANEL = (30, 45, 70)           # COLOUR_PANEL #1E2D46
_COLOUR_TEAM_BLUE = (60, 110, 210)     # COLOUR_TEAM_BLUE #3C6ED2
_COLOUR_TEAM_RED = (200, 60, 60)       # COLOUR_TEAM_RED
_COLOUR_TEXT_SECONDARY = (160, 175, 195)  # COLOUR_TEXT_SECONDARY #A0AFC3
_CARD_WIDTH = 720
_CARD_HEIGHT = 380
_CARD_BORDER_RADIUS = 12
_IMAGE_PANEL_SIZE = 240
_BUTTON_WIDTH = 200
_BUTTON_HEIGHT = 52
_COLOUR_BTN_PRIMARY = (41, 128, 185)   # COLOUR_BTN_PRIMARY #2980B9
_BUTTON_BORDER_RADIUS = 8
_SCRIM_ALPHA = 190


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_task_with_image() -> object:
    """Return a UnitTask with a valid image_path."""
    return UnitTask(  # type: ignore[misc]
        description="Do 20 situps",
        image_path=Path("mods/fitness_army/images/tasks/situps.gif"),
    )


@pytest.fixture
def mock_task_no_image() -> object:
    """Return a UnitTask with image_path=None."""
    return UnitTask(description="Do 10 pushups", image_path=None)  # type: ignore[misc]


def _make_overlay(
    task: object,
    capturing_side: object = None,
    capturing_unit_name: str = "Scout Rider",
    captured_unit_name: str = "Miner",
) -> object:
    """Factory that creates a TaskPopupOverlay with mocked pygame surface."""
    if capturing_side is None and PlayerSide is not None:
        capturing_side = PlayerSide.BLUE
    screen_mock = MagicMock()
    screen_mock.get_size.return_value = (1280, 720)
    return TaskPopupOverlay(  # type: ignore[misc]
        surface=screen_mock,
        task=task,
        capturing_side=capturing_side,
        capturing_unit_name=capturing_unit_name,
        captured_unit_name=captured_unit_name,
    )


# ---------------------------------------------------------------------------
# US-803 AC-1: Full-screen scrim covers entire PlayingScreen
# ---------------------------------------------------------------------------


class TestScrimLayout:
    """AC-1: Scrim covers 1280×720 at 75% alpha (#000000)."""

    def test_scrim_width_matches_screen(self, mock_task_no_image: object) -> None:
        """AC-1: scrim.width == screen width (1280)."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.scrim_rect.width == 1280  # type: ignore[union-attr]

    def test_scrim_height_matches_screen(self, mock_task_no_image: object) -> None:
        """AC-1: scrim.height == screen height (720)."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.scrim_rect.height == 720  # type: ignore[union-attr]

    def test_scrim_alpha_is_190(self, mock_task_no_image: object) -> None:
        """AC-1: scrim alpha is 190 (≈75% of 255)."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.scrim_alpha == _SCRIM_ALPHA  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-803 AC-2: Modal card dimensions and styling
# ---------------------------------------------------------------------------


class TestModalCardLayout:
    """AC-2: Modal card is 720×380 px, centred, with border_radius=12."""

    def test_card_width_is_720(self, mock_task_no_image: object) -> None:
        """AC-2: card width == 720."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.card_rect.width == _CARD_WIDTH  # type: ignore[union-attr]

    def test_card_height_is_380(self, mock_task_no_image: object) -> None:
        """AC-2: card height == 380."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.card_rect.height == _CARD_HEIGHT  # type: ignore[union-attr]

    def test_card_is_horizontally_centred(self, mock_task_no_image: object) -> None:
        """AC-2: card.centerx == screen_width // 2."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.card_rect.centerx == 1280 // 2  # type: ignore[union-attr]

    def test_card_is_vertically_centred(self, mock_task_no_image: object) -> None:
        """AC-2: card.centery == screen_height // 2."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.card_rect.centery == 720 // 2  # type: ignore[union-attr]

    def test_card_border_radius(self, mock_task_no_image: object) -> None:
        """AC-2: card border_radius == 12."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.card_border_radius == _CARD_BORDER_RADIUS  # type: ignore[union-attr]

    def test_card_background_colour(self, mock_task_no_image: object) -> None:
        """AC-2: card background is COLOUR_SURFACE (#283A58)."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.card_colour == _COLOUR_SURFACE  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-803 AC-3: Heading row content
# ---------------------------------------------------------------------------


class TestHeadingRow:
    """AC-3: Heading shows team dot, 'TASK ASSIGNED BY', team name, capture subtitle."""

    def test_heading_label_text(self, mock_task_no_image: object) -> None:
        """AC-3: heading_label == 'TASK ASSIGNED BY'."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.heading_label == "TASK ASSIGNED BY"  # type: ignore[union-attr]

    def test_heading_unit_text_for_blue(self, mock_task_no_image: object) -> None:
        """AC-3: heading for Blue team reads 'BLUE SCOUT RIDER'."""
        overlay = _make_overlay(
            mock_task_no_image,
            capturing_side=PlayerSide.BLUE,
            capturing_unit_name="Scout Rider",
        )
        assert overlay.heading_unit_text == "BLUE SCOUT RIDER"  # type: ignore[union-attr]

    def test_heading_unit_text_for_red(self, mock_task_no_image: object) -> None:
        """AC-3: heading for Red team reads 'RED SCOUT RIDER'."""
        overlay = _make_overlay(
            mock_task_no_image,
            capturing_side=PlayerSide.RED,
            capturing_unit_name="Scout Rider",
        )
        assert overlay.heading_unit_text == "RED SCOUT RIDER"  # type: ignore[union-attr]

    def test_team_dot_colour_blue(self, mock_task_no_image: object) -> None:
        """AC-3: team dot colour is COLOUR_TEAM_BLUE for Blue side."""
        overlay = _make_overlay(mock_task_no_image, capturing_side=PlayerSide.BLUE)
        assert overlay.team_dot_colour == _COLOUR_TEAM_BLUE  # type: ignore[union-attr]

    def test_team_dot_colour_red(self, mock_task_no_image: object) -> None:
        """AC-3: team dot colour is COLOUR_TEAM_RED for Red side."""
        overlay = _make_overlay(mock_task_no_image, capturing_side=PlayerSide.RED)
        assert overlay.team_dot_colour == _COLOUR_TEAM_RED  # type: ignore[union-attr]

    def test_subtitle_text(self, mock_task_no_image: object) -> None:
        """AC-3: subtitle reads 'Scout Rider captured your Miner!'."""
        overlay = _make_overlay(
            mock_task_no_image,
            capturing_unit_name="Scout Rider",
            captured_unit_name="Miner",
        )
        assert overlay.subtitle_text == "Scout Rider captured your Miner!"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-803 AC-4: Image panel with valid image
# ---------------------------------------------------------------------------


class TestImagePanel:
    """AC-4: Image panel is 240×240 px with letterboxing when image is valid."""

    def test_image_panel_width(self, mock_task_with_image: object) -> None:
        """AC-4: image_panel_rect.width == 240."""
        overlay = _make_overlay(mock_task_with_image)
        assert overlay.image_panel_rect.width == _IMAGE_PANEL_SIZE  # type: ignore[union-attr]

    def test_image_panel_height(self, mock_task_with_image: object) -> None:
        """AC-4: image_panel_rect.height == 240."""
        overlay = _make_overlay(mock_task_with_image)
        assert overlay.image_panel_rect.height == _IMAGE_PANEL_SIZE  # type: ignore[union-attr]

    def test_image_panel_background_colour(self, mock_task_with_image: object) -> None:
        """AC-4: image panel background is COLOUR_PANEL (#1E2D46)."""
        overlay = _make_overlay(mock_task_with_image)
        assert overlay.image_panel_colour == _COLOUR_PANEL  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-803 AC-5: Placeholder shown when image is None or unreadable
# ---------------------------------------------------------------------------


class TestImagePlaceholder:
    """AC-5: Placeholder '💪' shown when image_path is None."""

    def test_shows_placeholder_when_no_image(self, mock_task_no_image: object) -> None:
        """AC-5: task.image_path is None → use_placeholder is True."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.use_placeholder is True  # type: ignore[union-attr]

    def test_placeholder_text_is_flexed_arm(self, mock_task_no_image: object) -> None:
        """AC-5: placeholder_text == '💪'."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.placeholder_text == "💪"  # type: ignore[union-attr]

    def test_placeholder_panel_colour(self, mock_task_no_image: object) -> None:
        """AC-5: placeholder panel background is COLOUR_PANEL."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.image_panel_colour == _COLOUR_PANEL  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-803 AC-6: Text panel content
# ---------------------------------------------------------------------------


class TestTextPanel:
    """AC-6: Text panel shows 'Your task:' label, description, and instruction."""

    def test_task_label_text(self, mock_task_no_image: object) -> None:
        """AC-6: task_label == 'Your task:'."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.task_label == "Your task:"  # type: ignore[union-attr]

    def test_task_description_text(self, mock_task_no_image: object) -> None:
        """AC-6: task_description_text reflects the task's description."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.task_description_text == "Do 10 pushups"  # type: ignore[union-attr]

    def test_instruction_text(self, mock_task_no_image: object) -> None:
        """AC-6: instruction_text is the standard completion instruction."""
        overlay = _make_overlay(mock_task_no_image)
        expected = "Complete this exercise before your opponent continues."
        assert overlay.instruction_text == expected  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-803 AC-7: 'Complete ✓' button dimensions
# ---------------------------------------------------------------------------


class TestCompleteButton:
    """AC-7: 'Complete ✓' button is 200×52 px with correct styling."""

    def test_button_width(self, mock_task_no_image: object) -> None:
        """AC-7: button.width == 200."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.complete_button_rect.width == _BUTTON_WIDTH  # type: ignore[union-attr]

    def test_button_height(self, mock_task_no_image: object) -> None:
        """AC-7: button.height == 52."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.complete_button_rect.height == _BUTTON_HEIGHT  # type: ignore[union-attr]

    def test_button_label(self, mock_task_no_image: object) -> None:
        """AC-7: button label reads 'Complete ✓'."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.complete_button_label == "Complete ✓"  # type: ignore[union-attr]

    def test_button_background_colour(self, mock_task_no_image: object) -> None:
        """AC-7: button background is COLOUR_BTN_PRIMARY (#2980B9)."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.complete_button_colour == _COLOUR_BTN_PRIMARY  # type: ignore[union-attr]

    def test_button_border_radius(self, mock_task_no_image: object) -> None:
        """AC-7: button border_radius == 8."""
        overlay = _make_overlay(mock_task_no_image)
        assert overlay.complete_button_border_radius == _BUTTON_BORDER_RADIUS  # type: ignore[union-attr]
