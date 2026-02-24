"""
src/presentation/screens/main_menu_screen.py

MainMenuScreen — the application entry screen.
Specification: screen_flow.md §3.1
"""
from __future__ import annotations

from typing import Any

from src.presentation.screens.base import Screen

# Lazy import of pygame so the module works in headless test environments.
try:
    import pygame as _pygame

    _QUIT = _pygame.QUIT
    _KEYDOWN = _pygame.KEYDOWN
    _MOUSEBUTTONDOWN = _pygame.MOUSEBUTTONDOWN
except ImportError:
    _pygame = None  # type: ignore[assignment]
    _QUIT = 256
    _KEYDOWN = 768
    _MOUSEBUTTONDOWN = 1025

# Colour palette (aligned to ux-visual-style-guide.md §2)
_BG_COLOUR = (20, 30, 48)           # COLOUR_BG_MENU
_TITLE_COLOUR = (220, 180, 80)      # COLOUR_TITLE_GOLD
_SUBTITLE_COLOUR = (160, 185, 210)  # COLOUR_SUBTITLE
_DIVIDER_COLOUR = (50, 65, 95)      # COLOUR_PANEL_BORDER
_BTN_COLOUR = (50, 70, 100)         # COLOUR_BTN_DEFAULT
_BTN_HOVER_COLOUR = (72, 100, 144)  # COLOUR_BTN_HOVER
_BTN_DISABLED_COLOUR = (40, 50, 65) # COLOUR_BTN_DISABLED
_BTN_DANGER_COLOUR = (192, 57, 43)  # COLOUR_BTN_DANGER
_BTN_TEXT_COLOUR = (230, 230, 230)  # COLOUR_TEXT_PRIMARY
_BTN_TEXT_DISABLED = (100, 110, 125) # COLOUR_TEXT_DISABLED
_TEXT_SECONDARY = (160, 175, 195)   # COLOUR_TEXT_SECONDARY

_VERSION = "v1.0.0"
_COPYRIGHT = "© 2026"


class MainMenuScreen(Screen):
    """The main menu screen — the first screen shown when the application starts.

    Provides buttons for: Start Game, Continue (greyed out if no save),
    Load Game (stub), Settings (stub), and Quit.

    Specification: screen_flow.md §3.1
    """

    def __init__(self, screen_manager: Any, game_context: Any) -> None:
        """Initialise the main menu screen.

        Args:
            screen_manager: The ``ScreenManager`` for navigation.
            game_context: A ``_GameContext`` (or compatible) object that acts as
                a factory for new game sessions and holds shared resources such
                as the renderer and AI orchestrator.
        """
        self._screen_manager = screen_manager
        self._game_context = game_context
        self._font_large: Any = None
        self._font_medium: Any = None
        self._font_small: Any = None
        self._buttons: list[dict[str, Any]] = []
        self._mouse_pos: tuple[int, int] = (0, 0)

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, data: dict[str, Any]) -> None:
        """Initialise fonts and build button layout.

        Args:
            data: Context data (not used for the main menu).
        """
        if _pygame is None:
            return
        if not _pygame.get_init():
            _pygame.init()
        _pygame.font.init()
        self._font_large = _pygame.font.SysFont("Arial", 56, bold=True)
        self._font_medium = _pygame.font.SysFont("Arial", 32)
        self._font_small = _pygame.font.SysFont("Arial", 18)
        self._buttons = self._build_buttons()

    def on_exit(self) -> dict[str, Any]:
        """Return empty context — the main menu passes no data to child screens.

        Returns:
            Empty dictionary.
        """
        return {}

    def render(self, surface: Any) -> None:
        """Draw the main menu onto *surface*.

        Args:
            surface: The target ``pygame.Surface``.
        """
        if _pygame is None or surface is None:
            return

        w: int = surface.get_width()
        h: int = surface.get_height()

        # Background
        surface.fill(_BG_COLOUR)

        # Title (H — named "Conqueror's Quest" per wireframe annotation 1)
        if self._font_large is not None:
            title_surf = self._font_large.render("CONQUEROR'S QUEST", True, _TITLE_COLOUR)
            title_rect = title_surf.get_rect(center=(w // 2, h // 5))
            surface.blit(title_surf, title_rect)

        # Subtitle
        if self._font_small is not None:
            subtitle_surf = self._font_small.render(
                "A Stratego-inspired strategy game", True, _SUBTITLE_COLOUR
            )
            sub_rect = subtitle_surf.get_rect(center=(w // 2, h // 5 + 52))
            surface.blit(subtitle_surf, sub_rect)

            # Divider below subtitle
            divider_y = sub_rect.bottom + 18
            divider_x0 = w // 2 - 200
            divider_x1 = w // 2 + 200
            _pygame.draw.line(
                surface, _DIVIDER_COLOUR, (divider_x0, divider_y), (divider_x1, divider_y), 1
            )

        # Buttons
        for btn in self._buttons:
            is_danger = btn.get("danger", False)
            if btn["disabled"]:
                colour = _BTN_DISABLED_COLOUR
            elif btn["rect"].collidepoint(self._mouse_pos):
                colour = _BTN_HOVER_COLOUR
            elif is_danger:
                colour = _BTN_DANGER_COLOUR
            else:
                colour = _BTN_COLOUR
            _pygame.draw.rect(surface, colour, btn["rect"], border_radius=8)
            text_colour = _BTN_TEXT_DISABLED if btn["disabled"] else _BTN_TEXT_COLOUR
            if self._font_medium is not None:
                label = self._font_medium.render(btn["label"], True, text_colour)
                label_rect = label.get_rect(center=btn["rect"].center)
                surface.blit(label, label_rect)

        # Footer: version and copyright
        if self._font_small is not None:
            version_surf = self._font_small.render(_VERSION, True, _TEXT_SECONDARY)
            surface.blit(version_surf, (16, h - 28))
            copy_surf = self._font_small.render(_COPYRIGHT, True, _TEXT_SECONDARY)
            surface.blit(copy_surf, copy_surf.get_rect(right=w - 16, bottom=h - 8))

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
            self._quit()
            return

        if event.type == _MOUSEBUTTONDOWN and event.button == 1:
            for btn in self._buttons:
                if not btn["disabled"] and btn["rect"].collidepoint(event.pos):
                    btn["action"]()
                    return

    def update(self, delta_time: float) -> None:
        """Advance per-frame logic (no-op for the static main menu).

        Args:
            delta_time: Elapsed time since the previous frame, in seconds.
        """

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_buttons(self) -> list[dict[str, Any]]:
        """Return an ordered list of button descriptors for layout."""
        if _pygame is None:
            return []

        display_info = _pygame.display.Info()
        w = display_info.current_w or 1024
        h = display_info.current_h or 768

        btn_w, btn_h = 280, 52
        start_y = h // 2 - 40
        gap = 68

        def _rect(index: int) -> Any:
            x = w // 2 - btn_w // 2
            y = start_y + index * gap
            return _pygame.Rect(x, y, btn_w, btn_h)

        # Check whether a save file exists to enable / disable Continue.
        continue_disabled = True
        continue_action: Any = lambda: None  # noqa: E731
        try:
            most_recent = self._game_context.repository.get_most_recent_save()
            if most_recent is not None:
                continue_disabled = False
                continue_action = lambda: self._on_continue(most_recent)  # noqa: E731
        except Exception:  # noqa: BLE001
            pass

        return [
            {
                "label": "Start Game",
                "rect": _rect(0),
                "disabled": False,
                "danger": False,
                "action": self._on_start_game,
            },
            {
                "label": "Continue",
                "rect": _rect(1),
                "disabled": continue_disabled,
                "danger": False,
                "action": continue_action,
            },
            {
                "label": "Load Game",
                "rect": _rect(2),
                "disabled": False,
                "danger": False,
                "action": self._on_load_game,
            },
            {
                "label": "Settings \u2699",
                "rect": _rect(3),
                "disabled": False,
                "danger": False,
                "action": self._on_settings,
            },
            {
                "label": "Quit \u2715",
                "rect": _rect(4),
                "disabled": False,
                "danger": True,
                "action": self._quit,
            },
        ]

    def _on_start_game(self) -> None:
        """Navigate to the Start Game configuration screen."""
        from src.presentation.screens.start_game_screen import StartGameScreen

        start_screen = StartGameScreen(
            screen_manager=self._screen_manager,
            game_context=self._game_context,
        )
        self._screen_manager.push(start_screen)

    def _on_continue(self, save: Any) -> None:
        """Resume the most recent saved game.

        Args:
            save: The save-file object from the repository.
        """
        try:
            game_state = self._game_context.repository.load(save)
            self._game_context.resume_from_state(game_state, self._screen_manager)
        except Exception:  # noqa: BLE001
            pass  # Silently ignore if resuming is not yet implemented.

    def _on_load_game(self) -> None:
        """Open the Load Game screen."""
        from src.presentation.screens.load_game_screen import LoadGameScreen

        load_screen = LoadGameScreen(
            screen_manager=self._screen_manager,
            game_context=self._game_context,
        )
        self._screen_manager.push(load_screen)

    def _on_settings(self) -> None:
        """Open the Settings screen."""
        from src.presentation.screens.settings_screen import SettingsScreen

        settings_screen = SettingsScreen(
            screen_manager=self._screen_manager,
            game_context=self._game_context,
        )
        self._screen_manager.push(settings_screen)

    def _quit(self) -> None:
        """Post a QUIT event to end the application gracefully."""
        if _pygame is not None:
            _pygame.event.post(_pygame.event.Event(_pygame.QUIT))
