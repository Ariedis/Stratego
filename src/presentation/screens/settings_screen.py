"""
src/presentation/screens/settings_screen.py

SettingsScreen — display and audio configuration.
Specification: screen_flow.md §3.5; ux-wireframe-settings.md
"""
from __future__ import annotations

from typing import Any

from src.presentation.screens.base import Screen

# Lazy import of pygame so the module works in headless test environments.
try:
    import pygame as _pygame

    _QUIT = _pygame.QUIT
    _MOUSEBUTTONDOWN = _pygame.MOUSEBUTTONDOWN
except ImportError:
    _pygame = None  # type: ignore[assignment]
    _QUIT = 256
    _MOUSEBUTTONDOWN = 1025

# Colour palette (aligned to ux-visual-style-guide.md §2)
_BG_COLOUR = (20, 30, 48)            # COLOUR_BG_MENU
_TITLE_COLOUR = (220, 180, 80)       # COLOUR_TITLE_GOLD
_SUBTITLE_COLOUR = (160, 185, 210)   # COLOUR_SUBTITLE
_PANEL_BORDER_COLOUR = (50, 65, 95)  # COLOUR_PANEL_BORDER
_BTN_COLOUR = (50, 70, 100)          # COLOUR_BTN_DEFAULT
_BTN_HOVER_COLOUR = (72, 100, 144)   # COLOUR_BTN_HOVER
_BTN_PRIMARY_COLOUR = (41, 128, 185) # COLOUR_BTN_PRIMARY
_BTN_SELECTED_COLOUR = (45, 130, 70) # COLOUR_BTN_SELECTED (toggle ON)
_BTN_DANGER_COLOUR = (192, 57, 43)   # COLOUR_BTN_DANGER
_BTN_TEXT_COLOUR = (230, 230, 230)   # COLOUR_TEXT_PRIMARY
_TEXT_COLOUR = (230, 230, 230)       # COLOUR_TEXT_PRIMARY
_TEXT_SECONDARY = (160, 175, 195)    # COLOUR_TEXT_SECONDARY

# Default settings values
_DEFAULT_FULLSCREEN = False
_DEFAULT_FPS_CAP = 60
_DEFAULT_SFX_ENABLED = True
_DEFAULT_SFX_VOLUME = 75
_DEFAULT_MUSIC_ENABLED = True
_DEFAULT_MUSIC_VOLUME = 50
_DEFAULT_UNDO_ENABLED = False
_DEFAULT_REDUCE_MOTION = False
_DEFAULT_COLOUR_BLIND = False


class SettingsScreen(Screen):
    """Screen for configuring display, audio, and gameplay settings.

    Settings are read from ``game_context.config`` on entry and written
    back on "Apply".

    Specification: screen_flow.md §3.5; ux-wireframe-settings.md
    """

    def __init__(self, screen_manager: Any, game_context: Any) -> None:
        """Initialise the settings screen.

        Args:
            screen_manager: The ``ScreenManager`` for navigation.
            game_context: The ``_GameContext`` holding the ``Config`` object.
        """
        self._screen_manager = screen_manager
        self._game_context = game_context

        # Settings state (populated from config in on_enter)
        self._fullscreen: bool = _DEFAULT_FULLSCREEN
        self._fps_cap: int = _DEFAULT_FPS_CAP
        self._sfx_enabled: bool = _DEFAULT_SFX_ENABLED
        self._sfx_volume: int = _DEFAULT_SFX_VOLUME
        self._music_enabled: bool = _DEFAULT_MUSIC_ENABLED
        self._music_volume: int = _DEFAULT_MUSIC_VOLUME
        self._undo_enabled: bool = _DEFAULT_UNDO_ENABLED
        self._reduce_motion: bool = _DEFAULT_REDUCE_MOTION
        self._colour_blind: bool = _DEFAULT_COLOUR_BLIND

        self._font_title: Any = None
        self._font_medium: Any = None
        self._font_small: Any = None
        self._mouse_pos: tuple[int, int] = (0, 0)
        self._buttons: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public accessors (used by tests)
    # ------------------------------------------------------------------

    @property
    def fullscreen(self) -> bool:
        """Whether fullscreen mode is enabled."""
        return self._fullscreen

    @property
    def fps_cap(self) -> int:
        """Current FPS cap setting."""
        return self._fps_cap

    @property
    def sfx_enabled(self) -> bool:
        """Whether sound effects are enabled."""
        return self._sfx_enabled

    @property
    def music_enabled(self) -> bool:
        """Whether music is enabled."""
        return self._music_enabled

    @property
    def undo_enabled(self) -> bool:
        """Whether the undo feature is enabled."""
        return self._undo_enabled

    @property
    def reduce_motion(self) -> bool:
        """Whether reduce-motion accessibility mode is enabled."""
        return self._reduce_motion

    @property
    def colour_blind(self) -> bool:
        """Whether colour-blind accessibility mode is enabled."""
        return self._colour_blind

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, data: dict[str, Any]) -> None:
        """Load settings from the config and initialise fonts.

        Args:
            data: Context data (not used).
        """
        try:
            cfg = self._game_context.config
            self._fullscreen = getattr(cfg.display, "fullscreen", _DEFAULT_FULLSCREEN)
            self._fps_cap = getattr(cfg.display, "fps_cap", _DEFAULT_FPS_CAP)
            self._sfx_enabled = getattr(cfg, "sfx_enabled", _DEFAULT_SFX_ENABLED)
            self._sfx_volume = getattr(cfg, "sfx_volume", _DEFAULT_SFX_VOLUME)
            self._music_enabled = getattr(cfg, "music_enabled", _DEFAULT_MUSIC_ENABLED)
            self._music_volume = getattr(cfg, "music_volume", _DEFAULT_MUSIC_VOLUME)
            self._undo_enabled = getattr(cfg, "undo_enabled", _DEFAULT_UNDO_ENABLED)
            self._reduce_motion = getattr(cfg, "reduce_motion", _DEFAULT_REDUCE_MOTION)
            self._colour_blind = getattr(cfg, "colour_blind", _DEFAULT_COLOUR_BLIND)
        except Exception:  # noqa: BLE001
            pass

        if _pygame is None:
            return
        if not _pygame.get_init():
            _pygame.init()
        _pygame.font.init()
        self._font_title = _pygame.font.SysFont("Arial", 44, bold=True)
        self._font_medium = _pygame.font.SysFont("Arial", 28)
        self._font_small = _pygame.font.SysFont("Arial", 18)
        self._buttons = self._build_buttons()

    def on_exit(self) -> dict[str, Any]:
        """Return empty context.

        Returns:
            Empty dictionary.
        """
        return {}

    def render(self, surface: Any) -> None:
        """Draw the settings screen onto *surface*.

        Args:
            surface: The target ``pygame.Surface``.
        """
        if _pygame is None or surface is None:
            return

        w: int = surface.get_width()
        h: int = surface.get_height()
        surface.fill(_BG_COLOUR)

        # Title
        if self._font_title is not None:
            title_surf = self._font_title.render("Settings", True, _TITLE_COLOUR)
            surface.blit(title_surf, title_surf.get_rect(center=(w // 2, 60)))

        # Section headers and toggle rows
        rows = [
            ("Display", None, None),
            ("Fullscreen", "fullscreen", self._fullscreen),
            ("Undo", None, None),
            ("Undo", "undo_enabled", self._undo_enabled),
            ("Accessibility", None, None),
            ("Reduce Motion", "reduce_motion", self._reduce_motion),
            ("Colour Blind Mode", "colour_blind", self._colour_blind),
        ]
        if self._font_medium is not None and self._font_small is not None:
            y = 120
            gap = 48
            label_x = w // 4
            for title_text, field, state in rows:
                if field is None:
                    # Section header
                    hdr = self._font_medium.render(
                        f"\u2015\u2015 {title_text} \u2015\u2015",
                        True, _SUBTITLE_COLOUR,
                    )
                    surface.blit(hdr, (label_x, y))
                    y += gap - 8
                    _pygame.draw.line(
                        surface, _PANEL_BORDER_COLOUR,
                        (label_x, y), (w - label_x, y), 1,
                    )
                    y += 10
                else:
                    lbl = self._font_medium.render(title_text, True, _TEXT_COLOUR)
                    surface.blit(lbl, (label_x, y + 8))
                    # Toggle pill
                    pill_x = w * 3 // 4
                    pill_rect = _pygame.Rect(pill_x, y + 8, 60, 28)
                    pill_colour = _BTN_SELECTED_COLOUR if state else _BTN_COLOUR
                    _pygame.draw.rect(surface, pill_colour, pill_rect, border_radius=14)
                    thumb_x = pill_rect.right - 18 if state else pill_rect.left + 4
                    thumb_rect = _pygame.Rect(thumb_x, pill_rect.y + 4, 20, 20)
                    _pygame.draw.ellipse(surface, _TEXT_COLOUR, thumb_rect)
                    y += gap

        # Footer buttons
        for btn in self._buttons:
            is_hovered = btn["rect"].collidepoint(self._mouse_pos)
            colour = _BTN_HOVER_COLOUR if is_hovered else btn.get("colour", _BTN_COLOUR)
            _pygame.draw.rect(surface, colour, btn["rect"], border_radius=8)
            font = btn.get("font") or self._font_medium
            if font is not None:
                lbl_surf = font.render(btn["label"], True, _BTN_TEXT_COLOUR)
                surface.blit(lbl_surf, lbl_surf.get_rect(center=btn["rect"].center))

    def handle_event(self, event: Any) -> None:
        """Process a single input event.

        Args:
            event: A pygame event (or ``None`` in headless mode).
        """
        if event is None or _pygame is None:
            return

        if event.type == _pygame.MOUSEMOTION:
            self._mouse_pos = event.pos

        if event.type == _QUIT:
            _pygame.event.post(_pygame.event.Event(_pygame.QUIT))
            return

        if event.type == _MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

    def update(self, delta_time: float) -> None:
        """Advance per-frame logic (no-op for the static settings screen).

        Args:
            delta_time: Elapsed time since the previous frame, in seconds.
        """

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_buttons(self) -> list[dict[str, Any]]:
        """Return the footer button list."""
        if _pygame is None:
            return []

        display_info = _pygame.display.Info()
        w = display_info.current_w or 1024
        h = display_info.current_h or 768

        nav_y = h - 80
        btn_w, btn_h = 160, 48
        cx = w // 2

        return [
            {
                "label": "Reset",
                "rect": _pygame.Rect(cx - 2 * (btn_w + 20), nav_y, btn_w, btn_h),
                "colour": _BTN_DANGER_COLOUR,
                "action": self._on_reset,
                "font": self._font_medium,
            },
            {
                "label": "\u2190 Back",
                "rect": _pygame.Rect(cx - btn_w // 2 - 20, nav_y, btn_w, btn_h),
                "colour": _BTN_COLOUR,
                "action": self._on_back,
                "font": self._font_medium,
            },
            {
                "label": "\u2713 Apply",
                "rect": _pygame.Rect(cx + btn_w // 2 - 60, nav_y, btn_w, btn_h),
                "colour": _BTN_PRIMARY_COLOUR,
                "action": self._on_apply,
                "font": self._font_medium,
            },
        ]

    def _handle_click(self, pixel_pos: tuple[int, int]) -> None:
        """Route a click to the appropriate action."""
        if _pygame is None:
            return
        for btn in self._buttons:
            if btn["rect"].collidepoint(pixel_pos):
                btn["action"]()
                return

    def _on_back(self) -> None:
        """Return to the Main Menu without saving."""
        self._screen_manager.pop()

    def _on_apply(self) -> None:
        """Write current settings to config and return to the Main Menu."""
        try:
            self._game_context.config.display.fullscreen = self._fullscreen
            self._game_context.config.display.fps_cap = self._fps_cap
        except Exception:  # noqa: BLE001
            pass
        self._screen_manager.pop()

    def _on_reset(self) -> None:
        """Restore all settings to factory defaults."""
        self._fullscreen = _DEFAULT_FULLSCREEN
        self._fps_cap = _DEFAULT_FPS_CAP
        self._sfx_enabled = _DEFAULT_SFX_ENABLED
        self._sfx_volume = _DEFAULT_SFX_VOLUME
        self._music_enabled = _DEFAULT_MUSIC_ENABLED
        self._music_volume = _DEFAULT_MUSIC_VOLUME
        self._undo_enabled = _DEFAULT_UNDO_ENABLED
        self._reduce_motion = _DEFAULT_REDUCE_MOTION
        self._colour_blind = _DEFAULT_COLOUR_BLIND
