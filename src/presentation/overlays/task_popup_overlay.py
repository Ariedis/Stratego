"""
src/presentation/overlays/task_popup_overlay.py

TaskPopupOverlay — full-screen modal overlay shown to the captured player
after a combat event when the winning unit has tasks configured.

Specification: ux-wireframe-task-popup.md; screen_flow.md §3.7
Epic: EPIC-8 (US-803, US-804, US-805, US-806, US-809)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Lazy pygame import — overlay must be constructable in headless test mode.
try:
    import pygame as _pygame

    _KEYDOWN = _pygame.KEYDOWN
    _MOUSEBUTTONDOWN = _pygame.MOUSEBUTTONDOWN
    _K_RETURN = _pygame.K_RETURN
    _K_SPACE = _pygame.K_SPACE
    _K_TAB = _pygame.K_TAB
    _K_ESCAPE = _pygame.K_ESCAPE
except ImportError:
    _pygame = None  # type: ignore[assignment]
    _KEYDOWN = 768
    _MOUSEBUTTONDOWN = 1025
    _K_RETURN = 13
    _K_SPACE = 32
    _K_TAB = 9
    _K_ESCAPE = 27

# ---------------------------------------------------------------------------
# Colour palette (from ux-wireframe-task-popup.md §3; ux-visual-style-guide.md)
# ---------------------------------------------------------------------------

COLOUR_SURFACE = (40, 58, 88)           # #283A58  — card background
COLOUR_PANEL = (30, 45, 70)             # #1E2D46  — heading / image panel bg
COLOUR_TEAM_BLUE = (60, 110, 210)       # #3C6ED2
COLOUR_TEAM_RED = (200, 60, 60)         # #C83C3C
COLOUR_TEXT_SECONDARY = (160, 175, 195) # #A0AFC3
COLOUR_BTN_PRIMARY = (41, 128, 185)     # #2980B9
COLOUR_BTN_HOVER = (72, 100, 144)       # #486490
COLOUR_BTN_ACTIVE = (36, 54, 80)        # #243650
COLOUR_FOCUS_RING = (243, 156, 18)      # #F39C12

# ---------------------------------------------------------------------------
# Simple Rect helper — used when pygame is unavailable in headless tests
# ---------------------------------------------------------------------------


@dataclass
class _Rect:
    """Minimal pygame.Rect substitute for headless environments.

    Attributes:
        x: Left edge pixel coordinate.
        y: Top edge pixel coordinate.
        width: Width in pixels.
        height: Height in pixels.
    """

    x: int
    y: int
    width: int
    height: int

    @property
    def centerx(self) -> int:
        """Horizontal centre of the rectangle."""
        return self.x + self.width // 2

    @property
    def centery(self) -> int:
        """Vertical centre of the rectangle."""
        return self.y + self.height // 2

    @property
    def center(self) -> tuple[int, int]:
        """(centerx, centery) tuple."""
        return (self.centerx, self.centery)

    @property
    def right(self) -> int:
        """Right edge pixel coordinate."""
        return self.x + self.width

    @property
    def bottom(self) -> int:
        """Bottom edge pixel coordinate."""
        return self.y + self.height

    def collidepoint(self, pos: tuple[int, int]) -> bool:
        """Return True if *pos* is within this rectangle."""
        px, py = pos
        return self.x <= px < self.right and self.y <= py < self.bottom


def _make_rect(x: int, y: int, w: int, h: int) -> Any:
    """Return a Rect-like object using pygame.Rect when available, else _Rect."""
    if _pygame is not None:
        try:
            return _pygame.Rect(x, y, w, h)
        except Exception:  # noqa: BLE001,S110
            pass
    return _Rect(x, y, w, h)


# ---------------------------------------------------------------------------
# TaskPopupOverlay
# ---------------------------------------------------------------------------


class TaskPopupOverlay:
    """Full-screen modal overlay that shows a unit task to the captured player.

    Displayed after combat resolves when the capturing unit's
    :class:`~src.domain.army_mod.UnitCustomisation` has at least one task.
    The overlay blocks all board input until the player clicks "Complete ✓"
    (or presses Enter/Space while the button is focused).

    Specification: ux-wireframe-task-popup.md §2–§4; US-803, US-805, US-806, US-809.

    Args:
        surface: The pygame surface (or a mock with ``get_size()``) onto which
            the overlay will be rendered.
        task: The :class:`~src.domain.army_mod.UnitTask` to display.
        capturing_side: The :class:`~src.domain.enums.PlayerSide` of the unit
            that won combat.
        capturing_unit_name: Display name of the capturing unit (e.g.
            ``"Scout Rider"``).
        captured_unit_name: Display name of the captured unit (e.g. ``"Miner"``).
        captured_player_side: Side of the player whose piece was captured.
            Required for the 2-player handover prompt (US-809).
        game_mode: ``"TWO_PLAYER"`` or ``"VS_AI"`` — controls the handover
            sub-line visibility (US-809).
        gif_frames: Pre-extracted list of pygame Surface frames for an animated
            GIF image.  Pass ``None`` or an empty list for static images.
        frame_duration_ms: Duration of each GIF frame in milliseconds.
            Pass ``0.0`` to disable animation (static image).
        on_dismiss: Optional callable invoked when the popup is dismissed.
    """

    # ------------------------------------------------------------------
    # Layout constants (1280 × 720 reference resolution)
    # ------------------------------------------------------------------
    _CARD_WIDTH = 720
    _CARD_HEIGHT = 380
    _CARD_BORDER_RADIUS = 12
    _HEADING_HEIGHT = 72
    _IMAGE_PANEL_SIZE = 240
    _IMAGE_PANEL_PADDING = 16
    _BTN_WIDTH = 200
    _BTN_HEIGHT = 52
    _BTN_BORDER_RADIUS = 8
    _BTN_MARGIN = 16
    _SCRIM_ALPHA = 190
    _TEAM_DOT_RADIUS = 10

    def __init__(
        self,
        surface: Any,
        task: Any,
        capturing_side: Any,
        capturing_unit_name: str,
        captured_unit_name: str,
        captured_player_side: Any = None,
        game_mode: str | None = None,
        gif_frames: list[Any] | None = None,
        frame_duration_ms: float = 0.0,
        on_dismiss: Any = None,
    ) -> None:
        """Initialise the overlay and compute all layout rects."""
        self._surface = surface
        self._task = task
        self._capturing_side = capturing_side
        self._capturing_unit_name = capturing_unit_name
        self._captured_unit_name = captured_unit_name
        self._captured_player_side = captured_player_side
        self._game_mode = game_mode
        self._on_dismiss = on_dismiss

        # Visibility and input state
        self.is_visible: bool = True
        self._button_focused: bool = True

        # GIF animation state
        self._gif_frames: list[Any] = gif_frames if gif_frames is not None else []
        self._frame_duration_ms: float = frame_duration_ms
        self._frame_timer: float = 0.0
        self._current_frame_index: int = 0
        self._animation_active: bool = (
            len(self._gif_frames) > 1 and self._frame_duration_ms > 0.0
        )

        # Compute layout
        screen_w, screen_h = surface.get_size()
        self._screen_w = screen_w
        self._screen_h = screen_h
        self._compute_layout(screen_w, screen_h)

        # Derive text content
        self._compute_text_content(capturing_side, capturing_unit_name, captured_unit_name)
        self._compute_handover_content(captured_player_side, game_mode)

    # ------------------------------------------------------------------
    # Layout computation
    # ------------------------------------------------------------------

    def _compute_layout(self, screen_w: int, screen_h: int) -> None:
        """Compute all Rect objects from the reference screen dimensions."""
        # Scrim — full screen
        self._scrim_rect = _make_rect(0, 0, screen_w, screen_h)

        # Modal card — centred
        card_x = (screen_w - self._CARD_WIDTH) // 2
        card_y = (screen_h - self._CARD_HEIGHT) // 2
        self._card_rect = _make_rect(card_x, card_y, self._CARD_WIDTH, self._CARD_HEIGHT)

        # Image panel — left third of content row
        content_y = card_y + self._HEADING_HEIGHT
        img_x = card_x + self._IMAGE_PANEL_PADDING
        img_y = content_y + self._IMAGE_PANEL_PADDING
        img_sz = self._IMAGE_PANEL_SIZE
        self._image_panel_rect = _make_rect(img_x, img_y, img_sz, img_sz)

        # Complete button — bottom-right of text panel with 16 px margin
        btn_x = (
            card_x + self._CARD_WIDTH - self._BTN_WIDTH - self._BTN_MARGIN
        )
        btn_y = (
            card_y + self._CARD_HEIGHT - self._BTN_HEIGHT - self._BTN_MARGIN
        )
        self._complete_button_rect = _make_rect(btn_x, btn_y, self._BTN_WIDTH, self._BTN_HEIGHT)

    def _compute_text_content(
        self, capturing_side: Any, capturing_unit_name: str, captured_unit_name: str
    ) -> None:
        """Derive all static text strings from constructor arguments."""
        try:
            from src.domain.enums import PlayerSide

            is_blue = capturing_side == PlayerSide.BLUE
        except ImportError:
            is_blue = str(capturing_side).upper() == "BLUE"

        self._team_name = "BLUE" if is_blue else "RED"
        self._team_dot_colour: tuple[int, int, int] = (
            COLOUR_TEAM_BLUE if is_blue else COLOUR_TEAM_RED
        )
        self._heading_label = "TASK ASSIGNED BY"
        self._heading_unit_text = f"{self._team_name} {capturing_unit_name.upper()}"
        self._subtitle_text = f"{capturing_unit_name} captured your {captured_unit_name}!"
        self._task_label = "Your task:"
        self._task_description_text: str = self._task.description
        self._instruction_text = (
            "Complete this exercise before your opponent continues."
        )
        self._complete_button_label = "Complete \u2713"

    def _compute_handover_content(
        self, captured_player_side: Any, game_mode: str | None
    ) -> None:
        """Derive 2-player handover sub-line state (US-809)."""
        try:
            from src.presentation.screens.start_game_screen import GAME_MODE_TWO_PLAYER
        except ImportError:
            GAME_MODE_TWO_PLAYER = "TWO_PLAYER"

        self._show_handover_prompt = game_mode == GAME_MODE_TWO_PLAYER

        if captured_player_side is not None:
            try:
                from src.domain.enums import PlayerSide

                colour_name = (
                    "Blue"
                    if captured_player_side == PlayerSide.BLUE
                    else "Red"
                )
            except ImportError:
                colour_name = str(captured_player_side).capitalize()
            self._handover_prompt_text = f"Pass the device to {colour_name} player"
        else:
            self._handover_prompt_text = ""

    # ------------------------------------------------------------------
    # Public layout / style properties (read by tests and renderer)
    # ------------------------------------------------------------------

    @property
    def scrim_rect(self) -> Any:
        """Full-screen scrim rectangle."""
        return self._scrim_rect

    @property
    def scrim_alpha(self) -> int:
        """Scrim alpha value (190 ≈ 75 % opacity)."""
        return self._SCRIM_ALPHA

    @property
    def card_rect(self) -> Any:
        """Modal card rectangle."""
        return self._card_rect

    @property
    def card_border_radius(self) -> int:
        """Card corner border radius in pixels."""
        return self._CARD_BORDER_RADIUS

    @property
    def card_colour(self) -> tuple[int, int, int]:
        """Card background colour (COLOUR_SURFACE)."""
        return COLOUR_SURFACE

    @property
    def heading_label(self) -> str:
        """Static label part of the heading: 'TASK ASSIGNED BY'."""
        return self._heading_label

    @property
    def heading_unit_text(self) -> str:
        """Team + unit name part of the heading, e.g. 'BLUE SCOUT RIDER'."""
        return self._heading_unit_text

    @property
    def team_dot_colour(self) -> tuple[int, int, int]:
        """Filled team-colour dot colour (COLOUR_TEAM_BLUE or COLOUR_TEAM_RED)."""
        return self._team_dot_colour

    @property
    def subtitle_text(self) -> str:
        """Capture subtitle, e.g. 'Scout Rider captured your Miner!'."""
        return self._subtitle_text

    @property
    def image_panel_rect(self) -> Any:
        """Image/placeholder panel rectangle (240 × 240 px)."""
        return self._image_panel_rect

    @property
    def image_panel_colour(self) -> tuple[int, int, int]:
        """Image panel background colour (COLOUR_PANEL)."""
        return COLOUR_PANEL

    @property
    def use_placeholder(self) -> bool:
        """True when no valid task image is available ('💪' placeholder shown)."""
        return self._task.image_path is None

    @property
    def placeholder_text(self) -> str:
        """Placeholder emoji string shown when no image is available."""
        return "\U0001f4aa"  # 💪

    @property
    def task_label(self) -> str:
        """'Your task:' label above the task description."""
        return self._task_label

    @property
    def task_description_text(self) -> str:
        """The task description string from the mod."""
        return self._task_description_text

    @property
    def instruction_text(self) -> str:
        """Instruction text below the task description."""
        return self._instruction_text

    @property
    def complete_button_rect(self) -> Any:
        """'Complete ✓' button rectangle (200 × 52 px)."""
        return self._complete_button_rect

    @property
    def complete_button_label(self) -> str:
        """Button label string."""
        return self._complete_button_label

    @property
    def complete_button_colour(self) -> tuple[int, int, int]:
        """Button background colour (COLOUR_BTN_PRIMARY)."""
        return COLOUR_BTN_PRIMARY

    @property
    def complete_button_border_radius(self) -> int:
        """Button corner border radius in pixels."""
        return self._BTN_BORDER_RADIUS

    @property
    def button_focused(self) -> bool:
        """True when the 'Complete ✓' button has keyboard focus."""
        return self._button_focused

    @button_focused.setter
    def button_focused(self, value: bool) -> None:
        """Set keyboard focus state on the button."""
        self._button_focused = value

    # ------------------------------------------------------------------
    # GIF animation properties
    # ------------------------------------------------------------------

    @property
    def current_frame_index(self) -> int:
        """Index of the currently displayed GIF frame."""
        return self._current_frame_index

    @property
    def animation_active(self) -> bool:
        """True while the GIF animation is running."""
        return self._animation_active

    # ------------------------------------------------------------------
    # Handover prompt properties (US-809)
    # ------------------------------------------------------------------

    @property
    def show_handover_prompt(self) -> bool:
        """True when the '2-player pass device' sub-line should be shown."""
        return self._show_handover_prompt

    @property
    def handover_prompt_text(self) -> str:
        """The handover sub-line text, e.g. 'Pass the device to Red player'."""
        return self._handover_prompt_text

    # ------------------------------------------------------------------
    # Event handling (US-805)
    # ------------------------------------------------------------------

    def handle_event(self, event: Any) -> bool:
        """Process an input event; return True if the event was consumed.

        While the popup is visible:
        - All board-area mouse clicks are consumed.
        - Game-control keys (S, U, Q, arrows, Escape) are consumed without action.
        - Tab moves focus to the 'Complete ✓' button.
        - Enter / Space activate the button when focused (dismiss popup).
        - Click outside the card is consumed but does NOT dismiss.

        Args:
            event: A pygame event (or a mock with ``type`` and optional
                ``key`` / ``pos`` attributes).

        Returns:
            ``True`` if the event was consumed by the popup, ``False``
            otherwise.
        """
        if not self.is_visible:
            return False

        event_type = getattr(event, "type", None)

        if event_type == _KEYDOWN:
            key = getattr(event, "key", None)
            if key in (_K_RETURN, _K_SPACE) and self._button_focused:
                self.dismiss()
                return True
            if key == _K_TAB:
                self._button_focused = True
                return True
            # All other keys (Escape, S, U, Q, arrows, etc.) are suppressed.
            return True

        if event_type == _MOUSEBUTTONDOWN:
            pos = getattr(event, "pos", (0, 0))
            # Check if click is on the Complete button
            if self._complete_button_rect.collidepoint(pos):
                self.dismiss()
            # All clicks consumed regardless (no click-outside-to-dismiss).
            return True

        return False

    # ------------------------------------------------------------------
    # Update (GIF animation timer) — US-806
    # ------------------------------------------------------------------

    def update(self, delta_time_ms: float = 0.0) -> None:
        """Advance the GIF frame timer by *delta_time_ms* milliseconds.

        Args:
            delta_time_ms: Elapsed time since the last frame, in milliseconds.
        """
        if not self._animation_active or not self._gif_frames:
            return

        self._frame_timer += delta_time_ms
        if self._frame_timer >= self._frame_duration_ms:
            self._frame_timer -= self._frame_duration_ms
            self._current_frame_index = (
                (self._current_frame_index + 1) % len(self._gif_frames)
            )

    # ------------------------------------------------------------------
    # Dismissal
    # ------------------------------------------------------------------

    def dismiss(self) -> None:
        """Stop animation and mark the popup as no longer visible.

        Invokes the ``on_dismiss`` callback (if provided) after the popup
        is hidden, so the calling screen can restore board input and
        advance turn management.
        """
        self._animation_active = False
        self.is_visible = False
        if self._on_dismiss is not None:
            self._on_dismiss()

    # ------------------------------------------------------------------
    # Rendering (pygame-dependent, no-op in headless mode)
    # ------------------------------------------------------------------

    def render(self, surface: Any) -> None:
        """Draw the overlay onto *surface*.

        Does nothing if pygame is unavailable (headless test mode).

        Args:
            surface: Target ``pygame.Surface``.
        """
        if _pygame is None or surface is None or not self.is_visible:
            return

        # Scrim
        scrim = _pygame.Surface((self._screen_w, self._screen_h), _pygame.SRCALPHA)
        scrim.fill((0, 0, 0, self._SCRIM_ALPHA))
        surface.blit(scrim, (0, 0))

        # Card background
        _pygame.draw.rect(
            surface, COLOUR_SURFACE, self._card_rect, border_radius=self._CARD_BORDER_RADIUS
        )

        # Heading row background
        heading_rect = _make_rect(
            self._card_rect.x, self._card_rect.y, self._CARD_WIDTH, self._HEADING_HEIGHT
        )
        _pygame.draw.rect(
            surface, COLOUR_PANEL, heading_rect,
            border_radius=self._CARD_BORDER_RADIUS,
        )

        # Complete button
        _pygame.draw.rect(
            surface,
            COLOUR_BTN_PRIMARY,
            self._complete_button_rect,
            border_radius=self._BTN_BORDER_RADIUS,
        )
