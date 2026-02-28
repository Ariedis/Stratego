"""
test_task_popup_gif.py — Unit tests for TaskPopupOverlay GIF animation.

Epic: EPIC-8 | User Story: US-806
Covers acceptance criteria: AC-1 through AC-4
Specification: ux-wireframe-task-popup.md §6; custom_armies.md §5.1
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

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
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def _make_surface_mock() -> MagicMock:
    s = MagicMock()
    s.get_size.return_value = (1280, 720)
    return s


def _make_gif_frames(count: int = 4) -> list:
    """Return a list of *count* mock pygame surfaces representing GIF frames."""
    return [MagicMock() for _ in range(count)]


def _make_overlay_with_frames(frames: list, frame_duration_ms: float = 200.0) -> object:
    """Create a TaskPopupOverlay pre-loaded with stub GIF frames."""
    task = UnitTask(  # type: ignore[misc]
        description="Do 20 situps",
        image_path=Path("mods/fitness/tasks/situps.gif"),
    )
    surface = _make_surface_mock()
    overlay = TaskPopupOverlay(  # type: ignore[misc]
        surface=surface,
        task=task,
        capturing_side=PlayerSide.BLUE,
        capturing_unit_name="Scout Rider",
        captured_unit_name="Miner",
        gif_frames=frames,
        frame_duration_ms=frame_duration_ms,
    )
    return overlay


def _make_overlay_static() -> object:
    """Create a TaskPopupOverlay with a static (single-frame) image."""
    task = UnitTask(  # type: ignore[misc]
        description="Do pushups",
        image_path=Path("mods/fitness/tasks/pushups.png"),
    )
    surface = _make_surface_mock()
    return TaskPopupOverlay(  # type: ignore[misc]
        surface=surface,
        task=task,
        capturing_side=PlayerSide.RED,
        capturing_unit_name="Miner",
        captured_unit_name="Scout",
        gif_frames=[MagicMock()],  # single frame → no animation
        frame_duration_ms=0.0,
    )


# ---------------------------------------------------------------------------
# US-806 AC-1: GIF cycles through all frames at native frame rate
# ---------------------------------------------------------------------------


class TestGifFrameCycling:
    """AC-1: GIF with 4 frames cycles through frames 0→1→2→3→0 at frame rate."""

    def test_initial_frame_is_zero(self) -> None:
        """AC-1: On creation, current frame index == 0."""
        frames = _make_gif_frames(4)
        overlay = _make_overlay_with_frames(frames, frame_duration_ms=200.0)
        assert overlay.current_frame_index == 0  # type: ignore[union-attr]

    def test_frame_advances_after_duration(self) -> None:
        """AC-1: After delta_time >= frame_duration_ms, frame index advances to 1."""
        frames = _make_gif_frames(4)
        overlay = _make_overlay_with_frames(frames, frame_duration_ms=200.0)
        overlay.update(delta_time_ms=200.0)  # type: ignore[union-attr]
        assert overlay.current_frame_index == 1  # type: ignore[union-attr]

    def test_frame_cycles_back_to_zero_after_last(self) -> None:
        """AC-1: After the last frame (index 3), cycle wraps back to index 0."""
        frames = _make_gif_frames(4)
        overlay = _make_overlay_with_frames(frames, frame_duration_ms=200.0)
        # Advance through all 4 frames (0→1→2→3→0)
        for _ in range(4):
            overlay.update(delta_time_ms=200.0)  # type: ignore[union-attr]
        assert overlay.current_frame_index == 0  # type: ignore[union-attr]

    def test_partial_delta_does_not_advance_frame(self) -> None:
        """AC-1: delta_time < frame_duration_ms → frame index stays at 0."""
        frames = _make_gif_frames(4)
        overlay = _make_overlay_with_frames(frames, frame_duration_ms=200.0)
        overlay.update(delta_time_ms=100.0)  # half the frame duration  # type: ignore[union-attr]
        assert overlay.current_frame_index == 0  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-806 AC-2: GIF timer uses overlay's own delta_time (independent of game loop)
# ---------------------------------------------------------------------------


class TestGifTimerIndependence:
    """AC-2: GIF frame timer advances via delta_time, independent of game-loop state."""

    def test_update_accepts_delta_time_parameter(self) -> None:
        """AC-2: overlay.update(delta_time_ms=X) advances the internal timer."""
        frames = _make_gif_frames(4)
        overlay = _make_overlay_with_frames(frames, frame_duration_ms=200.0)
        # Should not raise; timer must be advanced
        overlay.update(delta_time_ms=50.0)  # type: ignore[union-attr]
        # timer should be at 50 ms (not yet enough for a frame advance)
        assert overlay.current_frame_index == 0  # type: ignore[union-attr]

    def test_multiple_updates_accumulate_time(self) -> None:
        """AC-2: Three 70 ms updates accumulate to 210 ms → one frame advance."""
        frames = _make_gif_frames(4)
        overlay = _make_overlay_with_frames(frames, frame_duration_ms=200.0)
        for _ in range(3):
            overlay.update(delta_time_ms=70.0)  # type: ignore[union-attr]
        assert overlay.current_frame_index == 1  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-806 AC-3: Animation stops when 'Complete ✓' is activated
# ---------------------------------------------------------------------------


class TestGifStopsOnDismiss:
    """AC-3: GIF animation stops when the 'Complete ✓' button is activated."""

    def test_animation_active_while_popup_visible(self) -> None:
        """AC-3 (pre-condition): animation_active is True while popup is open."""
        frames = _make_gif_frames(4)
        overlay = _make_overlay_with_frames(frames, frame_duration_ms=200.0)
        assert overlay.animation_active is True  # type: ignore[union-attr]

    def test_animation_stops_after_dismiss(self) -> None:
        """AC-3: Calling dismiss() stops GIF animation (animation_active → False)."""
        frames = _make_gif_frames(4)
        overlay = _make_overlay_with_frames(frames, frame_duration_ms=200.0)
        overlay.dismiss()  # type: ignore[union-attr]
        assert overlay.animation_active is False  # type: ignore[union-attr]

    def test_frame_does_not_advance_after_dismiss(self) -> None:
        """AC-3: After dismiss, update() no longer advances the frame index."""
        frames = _make_gif_frames(4)
        overlay = _make_overlay_with_frames(frames, frame_duration_ms=200.0)
        overlay.dismiss()  # type: ignore[union-attr]
        overlay.update(delta_time_ms=200.0)  # type: ignore[union-attr]
        assert overlay.current_frame_index == 0  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# US-806 AC-4: Static PNG displayed without animation
# ---------------------------------------------------------------------------


class TestStaticImageNoAnimation:
    """AC-4: Static PNG (single frame) displayed without flickering or animation."""

    def test_static_image_frame_stays_at_zero(self) -> None:
        """AC-4: Single-frame image → frame index never advances from 0."""
        overlay = _make_overlay_static()
        overlay.update(delta_time_ms=1000.0)  # type: ignore[union-attr]
        assert overlay.current_frame_index == 0  # type: ignore[union-attr]

    def test_static_image_animation_not_active(self) -> None:
        """AC-4: Static image (frame_duration_ms=0) → animation_active is False."""
        overlay = _make_overlay_static()
        assert overlay.animation_active is False  # type: ignore[union-attr]
