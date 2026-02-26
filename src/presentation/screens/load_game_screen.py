"""
src/presentation/screens/load_game_screen.py

LoadGameScreen — browse and load previously saved game sessions.
Specification: screen_flow.md §3.4; ux-wireframe-load-game.md
"""
from __future__ import annotations

from typing import Any

from src.presentation.font_utils import load_font
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
_PANEL_COLOUR = (30, 45, 70)         # COLOUR_PANEL
_PANEL_BORDER_COLOUR = (50, 65, 95)  # COLOUR_PANEL_BORDER
_SURFACE_COLOUR = (40, 58, 88)       # COLOUR_SURFACE
_BTN_COLOUR = (50, 70, 100)          # COLOUR_BTN_DEFAULT
_BTN_HOVER_COLOUR = (72, 100, 144)   # COLOUR_BTN_HOVER
_BTN_PRIMARY_COLOUR = (41, 128, 185) # COLOUR_BTN_PRIMARY
_BTN_SELECTED_COLOUR = (45, 130, 70) # COLOUR_BTN_SELECTED
_BTN_DANGER_COLOUR = (192, 57, 43)   # COLOUR_BTN_DANGER
_BTN_DISABLED_COLOUR = (40, 50, 65)  # COLOUR_BTN_DISABLED
_BTN_TEXT_COLOUR = (230, 230, 230)   # COLOUR_TEXT_PRIMARY
_BTN_TEXT_DISABLED = (100, 110, 125) # COLOUR_TEXT_DISABLED
_TEXT_COLOUR = (230, 230, 230)       # COLOUR_TEXT_PRIMARY
_TEXT_SECONDARY = (160, 175, 195)    # COLOUR_TEXT_SECONDARY


class LoadGameScreen(Screen):
    """Screen that lists saved game sessions for loading.

    Displays a scrollable list of save files (newest first).  Selecting a
    row enables the Load and Delete buttons.  Confirming Load resumes the
    selected game session.

    If no save files exist, an empty-state message is shown with a
    "Start New Game" shortcut.

    Specification: screen_flow.md §3.4; ux-wireframe-load-game.md
    """

    def __init__(self, screen_manager: Any, game_context: Any) -> None:
        """Initialise the load-game screen.

        Args:
            screen_manager: The ``ScreenManager`` for navigation.
            game_context: The ``_GameContext`` that provides the
                ``repository`` and ``resume_from_state`` helpers.
        """
        self._screen_manager = screen_manager
        self._game_context = game_context

        self._saves: list[Any] = []
        self._selected_index: int = -1  # -1 means nothing selected

        self._font_title: Any = None
        self._font_medium: Any = None
        self._font_small: Any = None
        self._mouse_pos: tuple[int, int] = (0, 0)

    # ------------------------------------------------------------------
    # Public accessors (used by tests)
    # ------------------------------------------------------------------

    @property
    def saves(self) -> list[Any]:
        """Ordered list of save-file objects loaded from the repository."""
        return self._saves

    @property
    def selected_index(self) -> int:
        """Index of the currently selected save row, or -1 for none."""
        return self._selected_index

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, data: dict[str, Any]) -> None:
        """Load the save-file list from the repository.

        Args:
            data: Context data (not used).
        """
        self._selected_index = -1
        self._saves = []
        try:
            self._saves = list(self._game_context.repository.list_saves())
        except Exception:  # noqa: BLE001,S110
            pass

        if _pygame is None:
            return
        if not _pygame.get_init():
            _pygame.init()
        _pygame.font.init()
        self._font_title = load_font(_pygame.font, 44, bold=True)
        self._font_medium = load_font(_pygame.font, 28)
        self._font_small = load_font(_pygame.font, 18)

    def on_exit(self) -> dict[str, Any]:
        """Return empty context.

        Returns:
            Empty dictionary.
        """
        return {}

    def render(self, surface: Any) -> None:
        """Draw the load-game screen onto *surface*.

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
            title_surf = self._font_title.render("Load Game", True, _TITLE_COLOUR)
            surface.blit(title_surf, title_surf.get_rect(center=(w // 2, 60)))

        if not self._saves:
            # Empty state
            self._render_empty_state(surface, w, h)
        else:
            self._render_save_list(surface, w, h)

        # Back button (always visible)
        back_rect = self._back_button_rect(w, h)
        if back_rect is not None:
            is_hovered = back_rect.collidepoint(self._mouse_pos)
            colour = _BTN_HOVER_COLOUR if is_hovered else _BTN_COLOUR
            _pygame.draw.rect(surface, colour, back_rect, border_radius=8)
            if self._font_medium is not None:
                lbl = self._font_medium.render("\u2190 Back", True, _BTN_TEXT_COLOUR)
                surface.blit(lbl, lbl.get_rect(center=back_rect.center))

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
        """Advance per-frame logic (no-op).

        Args:
            delta_time: Elapsed time since the previous frame, in seconds.
        """

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _render_empty_state(self, surface: Any, w: int, h: int) -> None:
        """Render the empty-state message when no saves exist."""
        if _pygame is None or self._font_medium is None or self._font_small is None:
            return
        msg = self._font_medium.render("No saved games found.", True, _TEXT_COLOUR)
        surface.blit(msg, msg.get_rect(center=(w // 2, h // 2 - 20)))
        hint = self._font_small.render(
            "Start a new game to create your first save.", True, _TEXT_SECONDARY
        )
        surface.blit(hint, hint.get_rect(center=(w // 2, h // 2 + 20)))

        # "Start New Game" shortcut button
        btn_rect = _pygame.Rect(w // 2 - 120, h // 2 + 70, 240, 48)
        is_hovered = btn_rect.collidepoint(self._mouse_pos)
        colour = _BTN_HOVER_COLOUR if is_hovered else _BTN_PRIMARY_COLOUR
        _pygame.draw.rect(surface, colour, btn_rect, border_radius=8)
        lbl = self._font_medium.render("Start New Game", True, _BTN_TEXT_COLOUR)
        surface.blit(lbl, lbl.get_rect(center=btn_rect.center))

    def _render_save_list(self, surface: Any, w: int, h: int) -> None:
        """Render the scrollable list of save files."""
        if _pygame is None or self._font_medium is None:
            return
        list_x = w // 2 - 500
        list_y = 120
        row_h = 52
        list_w = 1000

        for i, save in enumerate(self._saves):
            row_rect = _pygame.Rect(list_x, list_y + i * row_h, list_w, row_h - 2)
            if i == self._selected_index:
                colour = _BTN_SELECTED_COLOUR
            elif row_rect.collidepoint(self._mouse_pos):
                colour = _SURFACE_COLOUR
            else:
                colour = _PANEL_COLOUR
            _pygame.draw.rect(surface, colour, row_rect, border_radius=4)
            _pygame.draw.line(
                surface, _PANEL_BORDER_COLOUR,
                (list_x, list_y + (i + 1) * row_h - 2),
                (list_x + list_w, list_y + (i + 1) * row_h - 2),
                1,
            )
            label_text = str(save) if save is not None else f"Save {i + 1}"
            lbl = self._font_medium.render(label_text, True, _TEXT_COLOUR)
            surface.blit(lbl, (list_x + 16, row_rect.centery - lbl.get_height() // 2))

        # Load + Delete buttons (only when a row is selected)
        if self._selected_index >= 0:
            btn_w, btn_h = 140, 48
            cx = w // 2
            load_rect = _pygame.Rect(cx + 20, h - 100, btn_w, btn_h)
            del_rect = _pygame.Rect(cx - 20 - btn_w, h - 100, btn_w, btn_h)

            load_hov = load_rect.collidepoint(self._mouse_pos)
            del_hov = del_rect.collidepoint(self._mouse_pos)

            _pygame.draw.rect(
                surface,
                _BTN_HOVER_COLOUR if load_hov else _BTN_PRIMARY_COLOUR,
                load_rect, border_radius=8,
            )
            _pygame.draw.rect(
                surface,
                _BTN_HOVER_COLOUR if del_hov else _BTN_DANGER_COLOUR,
                del_rect, border_radius=8,
            )
            lbl_load = self._font_medium.render("\u25b6 Load", True, _BTN_TEXT_COLOUR)
            lbl_del = self._font_medium.render("\U0001f5d1 Delete", True, _BTN_TEXT_COLOUR)
            surface.blit(lbl_load, lbl_load.get_rect(center=load_rect.center))
            surface.blit(lbl_del, lbl_del.get_rect(center=del_rect.center))

    def _back_button_rect(self, w: int, h: int) -> Any:
        """Return the pygame.Rect for the Back button."""
        if _pygame is None:
            return None
        return _pygame.Rect(40, h - 100, 140, 48)

    def _handle_click(self, pixel_pos: tuple[int, int]) -> None:
        """Route a left-click to the appropriate action."""
        if _pygame is None:
            return
        try:
            surface = _pygame.display.get_surface()
            w = surface.get_width() if surface else 1024
            h = surface.get_height() if surface else 768
        except Exception:  # noqa: BLE001
            w, h = 1024, 768

        back_rect = self._back_button_rect(w, h)
        if back_rect is not None and back_rect.collidepoint(pixel_pos):
            self._on_back()
            return

        # Check save list rows
        list_x = w // 2 - 500
        list_y = 120
        row_h = 52
        for i in range(len(self._saves)):
            row_rect = _pygame.Rect(list_x, list_y + i * row_h, 1000, row_h - 2)
            if row_rect.collidepoint(pixel_pos):
                self._selected_index = i
                return

        # Check Load / Delete buttons
        if self._selected_index >= 0:
            btn_w, btn_h = 140, 48
            cx = w // 2
            load_rect = _pygame.Rect(cx + 20, h - 100, btn_w, btn_h)
            del_rect = _pygame.Rect(cx - 20 - btn_w, h - 100, btn_w, btn_h)
            if load_rect.collidepoint(pixel_pos):
                self._on_load()
            elif del_rect.collidepoint(pixel_pos):
                self._on_delete()

        # Empty-state "Start New Game" button
        if not self._saves:
            btn_rect = _pygame.Rect(w // 2 - 120, h // 2 + 70, 240, 48)
            if btn_rect.collidepoint(pixel_pos):
                self._on_start_new_game()

    def _on_back(self) -> None:
        """Return to the Main Menu."""
        self._screen_manager.pop()

    def _on_load(self) -> None:
        """Load the selected save file and resume the game session."""
        if self._selected_index < 0 or self._selected_index >= len(self._saves):
            return
        save = self._saves[self._selected_index]
        try:
            game_state = self._game_context.repository.load(save)
            self._game_context.resume_from_state(game_state, self._screen_manager)
        except Exception:  # noqa: BLE001,S110
            pass  # Error handling deferred to future sprint.

    def _on_delete(self) -> None:
        """Delete the selected save file after confirmation (stub)."""
        if self._selected_index < 0 or self._selected_index >= len(self._saves):
            return
        save = self._saves[self._selected_index]
        try:
            self._game_context.repository.delete(save)
            self._saves.pop(self._selected_index)
            self._selected_index = -1
        except Exception:  # noqa: BLE001,S110
            pass

    def _on_start_new_game(self) -> None:
        """Navigate to StartGameScreen from the empty state."""
        from src.presentation.screens.start_game_screen import StartGameScreen

        self._screen_manager.replace(
            StartGameScreen(
                screen_manager=self._screen_manager,
                game_context=self._game_context,
            )
        )
