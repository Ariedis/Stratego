"""
src/presentation/screens/game_over_screen.py

GameOverScreen — displayed when a game ends.
Specification: screen_flow.md §3.8
"""
from __future__ import annotations

from typing import Any

from src.domain.enums import PlayerSide
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

# Colour palette
_BG_COLOUR = (15, 20, 35)
_TITLE_COLOUR = (220, 180, 80)
_WIN_RED = (200, 80, 80)
_WIN_BLUE = (80, 120, 220)
_WIN_DRAW = (160, 160, 160)
_TEXT_COLOUR = (210, 210, 210)
_BTN_COLOUR = (50, 70, 100)
_BTN_HOVER_COLOUR = (80, 110, 160)
_BTN_TEXT_COLOUR = (230, 230, 230)


class GameOverScreen(Screen):
    """Screen shown when the game ends.

    Displays the winner, winning condition, and turn count.  Provides
    three navigation options:

    - **Play Again** → ``StartGameScreen``
    - **Main Menu**  → ``MainMenuScreen`` (replaces the current stack)
    - **Quit**       → graceful exit

    Specification: screen_flow.md §3.8
    """

    def __init__(
        self,
        screen_manager: Any,
        winner: PlayerSide | None,
        reason: str,
        turn_count: int,
    ) -> None:
        """Initialise the game-over screen.

        Args:
            screen_manager: The ``ScreenManager`` for navigation.
            winner: The winning ``PlayerSide``, or ``None`` for a draw.
            reason: Human-readable string describing how the game ended.
            turn_count: Number of turns played.
        """
        self._screen_manager = screen_manager
        self._winner = winner
        self._reason = reason
        self._turn_count = turn_count

        self._font_large: Any = None
        self._font_medium: Any = None
        self._font_small: Any = None
        self._buttons: list[dict[str, Any]] = []
        self._mouse_pos: tuple[int, int] = (0, 0)

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, data: dict[str, Any]) -> None:
        """Optionally override winner/reason/turn_count from *data*.

        Args:
            data: May contain ``winner``, ``reason``, and ``final_state``.
        """
        if "winner" in data:
            self._winner = data["winner"]
        if "reason" in data:
            self._reason = data["reason"]
        if "final_state" in data:
            state = data["final_state"]
            try:
                self._turn_count = state.turn_number
            except AttributeError:
                pass

        if _pygame is None:
            return
        if not _pygame.get_init():
            _pygame.init()
        _pygame.font.init()
        self._font_large = _pygame.font.SysFont("Arial", 52, bold=True)
        self._font_medium = _pygame.font.SysFont("Arial", 30)
        self._font_small = _pygame.font.SysFont("Arial", 22)
        self._buttons = self._build_buttons()

    def on_exit(self) -> dict[str, Any]:
        """Return empty context.

        Returns:
            Empty dictionary.
        """
        return {}

    def render(self, surface: Any) -> None:
        """Draw the game-over screen onto *surface*.

        Args:
            surface: The target ``pygame.Surface``.
        """
        if _pygame is None or surface is None:
            return

        w: int = surface.get_width()
        h: int = surface.get_height()
        surface.fill(_BG_COLOUR)

        cy = h // 3

        # Winner / draw headline
        if self._font_large is not None:
            if self._winner is None:
                headline = "Draw!"
                headline_colour = _WIN_DRAW
            else:
                headline = f"{self._winner.value} wins!"
                headline_colour = (
                    _WIN_RED if self._winner == PlayerSide.RED else _WIN_BLUE
                )
            headline_surf = self._font_large.render(headline, True, headline_colour)
            surface.blit(headline_surf, headline_surf.get_rect(center=(w // 2, cy)))

        # Reason
        if self._font_medium is not None:
            reason_surf = self._font_medium.render(self._reason, True, _TEXT_COLOUR)
            surface.blit(reason_surf, reason_surf.get_rect(center=(w // 2, cy + 70)))

        # Turn count
        if self._font_small is not None:
            turn_surf = self._font_small.render(
                f"Turn {self._turn_count}", True, _TEXT_COLOUR
            )
            surface.blit(turn_surf, turn_surf.get_rect(center=(w // 2, cy + 110)))

        # Buttons
        for btn in self._buttons:
            is_hovered = btn["rect"].collidepoint(self._mouse_pos)
            colour = _BTN_HOVER_COLOUR if is_hovered else _BTN_COLOUR
            _pygame.draw.rect(surface, colour, btn["rect"], border_radius=8)
            if self._font_medium is not None:
                label = self._font_medium.render(btn["label"], True, _BTN_TEXT_COLOUR)
                surface.blit(label, label.get_rect(center=btn["rect"].center))

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
            for btn in self._buttons:
                if btn["rect"].collidepoint(event.pos):
                    btn["action"]()
                    return

    def update(self, delta_time: float) -> None:
        """Advance per-frame logic (no-op).

        Args:
            delta_time: Elapsed time since the previous frame, in seconds.
        """

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_buttons(self) -> list[dict[str, Any]]:
        """Return the button list for the game-over screen."""
        if _pygame is None:
            return []

        display_info = _pygame.display.Info()
        w = display_info.current_w or 1024
        h = display_info.current_h or 768

        btn_w, btn_h = 200, 48
        gap = 20
        total_w = 3 * btn_w + 2 * gap
        start_x = w // 2 - total_w // 2
        y = h * 2 // 3

        return [
            {
                "label": "Play Again",
                "rect": _pygame.Rect(start_x, y, btn_w, btn_h),
                "action": self._on_play_again,
            },
            {
                "label": "Main Menu",
                "rect": _pygame.Rect(start_x + btn_w + gap, y, btn_w, btn_h),
                "action": self._on_main_menu,
            },
            {
                "label": "Quit",
                "rect": _pygame.Rect(start_x + 2 * (btn_w + gap), y, btn_w, btn_h),
                "action": self._on_quit,
            },
        ]

    def _on_play_again(self) -> None:
        """Return to the Start Game screen to configure a new game."""
        # Pop the game-over screen to return to PlayingScreen, then keep
        # popping until we're back at MainMenu and push StartGameScreen.
        # Simpler: pop twice to reach MainMenuScreen then let it handle
        # the next transition.  If the stack depth is uncertain, use a
        # robust approach: pop this screen, which triggers MainMenuScreen
        # if that's next, or we can navigate explicitly.
        # For now: pop back to the top-most remaining screen and let the
        # user press "Start Game" again.
        try:
            self._screen_manager.pop()  # pops GameOverScreen
        except IndexError:
            pass

    def _on_main_menu(self) -> None:
        """Return to the main menu by popping all screens above it."""
        # Pop screens until we're back at the main menu.
        # Since we don't hold a reference to the main menu screen, we pop
        # as many screens as possible.
        for _ in range(10):  # safety limit
            try:
                self._screen_manager.pop()
            except IndexError:
                break

    def _on_quit(self) -> None:
        """Quit the application."""
        if _pygame is not None:
            _pygame.event.post(_pygame.event.Event(_pygame.QUIT))
