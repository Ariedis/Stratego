"""
src/presentation/screens/start_game_screen.py

StartGameScreen — game mode and difficulty configuration before a new game.
Specification: screen_flow.md §3.2
"""
from __future__ import annotations

from typing import Any

from src.domain.enums import PlayerType
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

# Colour palette — aligned to ux-visual-style-guide.md §2
_BG_COLOUR = (20, 30, 48)           # COLOUR_BG_MENU
_TITLE_COLOUR = (220, 180, 80)      # COLOUR_TITLE_GOLD
_BTN_COLOUR = (50, 70, 100)         # COLOUR_BTN_DEFAULT
_BTN_HOVER_COLOUR = (72, 100, 144)  # COLOUR_BTN_HOVER
_BTN_SELECTED_COLOUR = (45, 130, 70)  # COLOUR_BTN_SELECTED
_BTN_TEXT_COLOUR = (230, 230, 230)  # COLOUR_TEXT_PRIMARY
_LABEL_COLOUR = (160, 185, 210)     # COLOUR_SUBTITLE

# Game-mode identifiers (plain strings — no new enum required)
GAME_MODE_TWO_PLAYER = "TWO_PLAYER"
GAME_MODE_VS_AI = "VS_AI"

_DIFFICULTY_OPTIONS: list[tuple[str, PlayerType]] = [
    ("Easy", PlayerType.AI_EASY),
    ("Medium", PlayerType.AI_MEDIUM),
    ("Hard", PlayerType.AI_HARD),
]


class StartGameScreen(Screen):
    """Screen for choosing game mode (two-player or vs AI) and AI difficulty.

    Specification: screen_flow.md §3.2

    Navigation:
    - Confirm → pushes ``SetupScreen`` (via ``game_context.start_new_game``).
    - Back    → ``screen_manager.pop()`` returns to ``MainMenuScreen``.
    """

    def __init__(self, screen_manager: Any, game_context: Any) -> None:
        """Initialise the start game screen.

        Args:
            screen_manager: The ``ScreenManager`` for navigation.
            game_context: A ``_GameContext`` that provides the ``start_new_game``
                factory and shared resources (renderer, event bus, …).
        """
        self._screen_manager = screen_manager
        self._game_context = game_context

        # User selections (annotation 4: default to vs Computer / Medium)
        self._game_mode: str = GAME_MODE_VS_AI
        self._ai_difficulty: PlayerType = PlayerType.AI_MEDIUM

        self._font_title: Any = None
        self._font_medium: Any = None
        self._font_small: Any = None
        self._buttons: list[dict[str, Any]] = []
        self._mouse_pos: tuple[int, int] = (0, 0)

    # ------------------------------------------------------------------
    # Public accessors (used by tests)
    # ------------------------------------------------------------------

    @property
    def game_mode(self) -> str:
        """The currently selected game mode identifier."""
        return self._game_mode

    @property
    def ai_difficulty(self) -> PlayerType:
        """The currently selected AI difficulty level."""
        return self._ai_difficulty

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, data: dict[str, Any]) -> None:
        """Initialise fonts and build button layout.

        Args:
            data: Context data (not used).
        """
        if _pygame is None:
            return
        if not _pygame.get_init():
            _pygame.init()
        _pygame.font.init()
        self._font_title = _pygame.font.SysFont("Arial", 44, bold=True)
        self._font_medium = _pygame.font.SysFont("Arial", 30)
        self._font_small = _pygame.font.SysFont("Arial", 24)
        self._buttons = self._build_buttons()

    def on_exit(self) -> dict[str, Any]:
        """Return selected options to the previous screen.

        Returns:
            A dict with ``game_mode`` and ``ai_difficulty`` keys.
        """
        return {
            "game_mode": self._game_mode,
            "ai_difficulty": self._ai_difficulty,
        }

    def render(self, surface: Any) -> None:
        """Draw the start-game configuration screen onto *surface*.

        Args:
            surface: The target ``pygame.Surface``.
        """
        if _pygame is None or surface is None:
            return

        w: int = surface.get_width()
        surface.fill(_BG_COLOUR)

        # Title
        if self._font_title is not None:
            title = self._font_title.render("New Game", True, _TITLE_COLOUR)
            surface.blit(title, title.get_rect(center=(w // 2, 80)))

        # "Game Mode" section label
        if self._font_medium is not None:
            mode_label = self._font_medium.render("Game Mode", True, _LABEL_COLOUR)
            cx = w // 2
            surface.blit(mode_label, mode_label.get_rect(center=(cx, 148)))

        # Buttons
        for btn in self._buttons:
            is_selected = btn.get("selected", False)
            is_hovered = btn["rect"].collidepoint(self._mouse_pos)
            if is_selected:
                colour = _BTN_SELECTED_COLOUR
            elif is_hovered:
                colour = _BTN_HOVER_COLOUR
            else:
                colour = _BTN_COLOUR
            _pygame.draw.rect(surface, colour, btn["rect"], border_radius=8)

            font = btn.get("font") or self._font_medium
            if font is not None:
                # Prefix selected toggle buttons with a checkmark
                label_text = btn["label"]
                if is_selected and btn.get("is_toggle", False):
                    label_text = f"\u2713 {label_text}"
                label_surf = font.render(label_text, True, _BTN_TEXT_COLOUR)
                surface.blit(label_surf, label_surf.get_rect(center=btn["rect"].center))

        # AI difficulty label — only when vs AI is selected
        if self._game_mode == GAME_MODE_VS_AI and self._font_medium is not None:
            diff_label = self._font_medium.render(
                "AI Difficulty", True, _LABEL_COLOUR
            )
            surface.blit(diff_label, diff_label.get_rect(center=(w // 2, 298)))

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
                    # Rebuild buttons after a selection change
                    self._buttons = self._build_buttons()
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
        """Return the full button list, refreshed after each selection change."""
        if _pygame is None:
            return []

        display_info = _pygame.display.Info()
        w = display_info.current_w or 1024
        btn_w, btn_h = 200, 48
        gap = 14
        cx = w // 2

        buttons: list[dict[str, Any]] = []

        # --- Mode row ---
        mode_y = 180
        mode_label_offset = 220
        buttons.append({
            "label": "Local 2-Player",
            "rect": _pygame.Rect(cx - mode_label_offset, mode_y, btn_w, btn_h),
            "selected": self._game_mode == GAME_MODE_TWO_PLAYER,
            "is_toggle": True,
            "action": self._select_two_player,
            "font": self._font_medium,
        })
        buttons.append({
            "label": "vs Computer",
            "rect": _pygame.Rect(cx - mode_label_offset + btn_w + gap, mode_y, btn_w, btn_h),
            "selected": self._game_mode == GAME_MODE_VS_AI,
            "is_toggle": True,
            "action": self._select_vs_ai,
            "font": self._font_medium,
        })

        # --- Difficulty row (only when vs AI) ---
        if self._game_mode == GAME_MODE_VS_AI:
            diff_y = 360
            for i, (label, player_type) in enumerate(_DIFFICULTY_OPTIONS):
                x = cx - mode_label_offset + i * (btn_w + gap)
                buttons.append({
                    "label": label,
                    "rect": _pygame.Rect(x, diff_y, btn_w, btn_h),
                    "selected": self._ai_difficulty == player_type,
                    "is_toggle": True,
                    "action": self._make_difficulty_selector(player_type),
                    "font": self._font_small or self._font_medium,
                })

        # --- Navigation buttons (H4.4: Back on left, Confirm on right) ---
        nav_y = 520
        nav_btn_w = 160
        buttons.append({
            "label": "\u2190 Back",
            "rect": _pygame.Rect(cx - nav_btn_w - 20, nav_y, nav_btn_w, btn_h),
            "selected": False,
            "is_toggle": False,
            "action": self._on_back,
            "font": self._font_medium,
        })
        buttons.append({
            "label": "Confirm \u2192",
            "rect": _pygame.Rect(cx + 20, nav_y, nav_btn_w, btn_h),
            "selected": False,
            "is_toggle": False,
            "action": self._on_confirm,
            "font": self._font_medium,
        })

        return buttons

    # -- Selection helpers --

    def _select_two_player(self) -> None:
        """Switch to two-player mode."""
        self._game_mode = GAME_MODE_TWO_PLAYER

    def _select_vs_ai(self) -> None:
        """Switch to vs-AI mode."""
        self._game_mode = GAME_MODE_VS_AI

    def _make_difficulty_selector(self, difficulty: PlayerType) -> Any:
        """Return a closure that selects *difficulty* when called."""
        def _select() -> None:
            self._ai_difficulty = difficulty
        return _select

    def _on_back(self) -> None:
        """Return to the main menu."""
        self._screen_manager.pop()

    def _on_confirm(self) -> None:
        """Navigate to ArmySelectScreen to choose armies before setup."""
        from src.presentation.screens.army_select_screen import ArmySelectScreen

        army_screen = ArmySelectScreen(
            screen_manager=self._screen_manager,
            game_context=self._game_context,
            game_mode=self._game_mode,
            ai_difficulty=self._ai_difficulty if self._game_mode == GAME_MODE_VS_AI else None,
        )
        self._screen_manager.push(army_screen)
