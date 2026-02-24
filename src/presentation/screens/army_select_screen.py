"""
src/presentation/screens/army_select_screen.py

ArmySelectScreen — lets players choose their army variant before setup.
Specification: screen_flow.md §3.3; ux-wireframe-army-select.md
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
_PANEL_COLOUR = (30, 45, 70)         # COLOUR_PANEL
_PANEL_BORDER_COLOUR = (50, 65, 95)  # COLOUR_PANEL_BORDER
_SURFACE_COLOUR = (40, 58, 88)       # COLOUR_SURFACE
_BTN_COLOUR = (50, 70, 100)          # COLOUR_BTN_DEFAULT
_BTN_HOVER_COLOUR = (72, 100, 144)   # COLOUR_BTN_HOVER
_BTN_PRIMARY_COLOUR = (41, 128, 185) # COLOUR_BTN_PRIMARY
_BTN_TEXT_COLOUR = (230, 230, 230)   # COLOUR_TEXT_PRIMARY
_TEXT_SECONDARY = (160, 175, 195)    # COLOUR_TEXT_SECONDARY
_TEAM_RED_COLOUR = (200, 60, 60)     # COLOUR_TEAM_RED
_TEAM_BLUE_COLOUR = (60, 110, 210)   # COLOUR_TEAM_BLUE

# "Classic Army" is always available as the default option.
_CLASSIC_ARMY_NAME = "Classic Army"
_CLASSIC_ARMY_DESCRIPTION = "The original Stratego set.\n40 pieces · Standard ranks"


class ArmySelectScreen(Screen):
    """Screen for selecting army variants before the setup phase.

    In *vs Computer* mode only Player 1 (Red) selects an army.
    In *Local 2-Player* mode both players choose independently.

    After confirmation, calls ``game_context.start_new_game()`` to create
    the game session and push ``SetupScreen``.

    Specification: screen_flow.md §3.3; ux-wireframe-army-select.md
    """

    def __init__(
        self,
        screen_manager: Any,
        game_context: Any,
        game_mode: str,
        ai_difficulty: Any = None,
    ) -> None:
        """Initialise the army-select screen.

        Args:
            screen_manager: The ``ScreenManager`` for navigation.
            game_context: A ``_GameContext`` that provides the
                ``start_new_game`` factory.
            game_mode: ``"TWO_PLAYER"`` or ``"VS_AI"``.
            ai_difficulty: The selected ``PlayerType`` for the AI, or
                ``None`` for two-player mode.
        """
        self._screen_manager = screen_manager
        self._game_context = game_context
        self._game_mode = game_mode
        self._ai_difficulty = ai_difficulty

        # Army selection (only Classic Army supported in v1.0)
        self._player1_army: str = _CLASSIC_ARMY_NAME
        self._player2_army: str = _CLASSIC_ARMY_NAME

        self._font_title: Any = None
        self._font_medium: Any = None
        self._font_small: Any = None
        self._buttons: list[dict[str, Any]] = []
        self._mouse_pos: tuple[int, int] = (0, 0)

    # ------------------------------------------------------------------
    # Public accessors (used by tests)
    # ------------------------------------------------------------------

    @property
    def player1_army(self) -> str:
        """Selected army name for Player 1."""
        return self._player1_army

    @property
    def player2_army(self) -> str:
        """Selected army name for Player 2 (may equal Player 1 in 2-player mode)."""
        return self._player2_army

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, data: dict[str, Any]) -> None:
        """Initialise fonts and build the button layout.

        Args:
            data: Context data from ``StartGameScreen.on_exit()``.
                  May contain ``game_mode`` and ``ai_difficulty`` overrides.
        """
        if "game_mode" in data:
            self._game_mode = data["game_mode"]
        if "ai_difficulty" in data:
            self._ai_difficulty = data["ai_difficulty"]

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
        """Return selected army data to the next screen.

        Returns:
            A dict with ``game_mode``, ``ai_difficulty``, ``player1_army``,
            and ``player2_army`` keys.
        """
        return {
            "game_mode": self._game_mode,
            "ai_difficulty": self._ai_difficulty,
            "player1_army": self._player1_army,
            "player2_army": self._player2_army,
        }

    def render(self, surface: Any) -> None:
        """Draw the army-select screen onto *surface*.

        Args:
            surface: The target ``pygame.Surface``.
        """
        if _pygame is None or surface is None:
            return

        w: int = surface.get_width()
        surface.fill(_BG_COLOUR)

        # Screen title
        is_two_player = self._game_mode != "VS_AI"
        title_text = "Choose Your Armies" if is_two_player else "Choose Your Army"
        if self._font_title is not None:
            title_surf = self._font_title.render(title_text, True, _TITLE_COLOUR)
            surface.blit(title_surf, title_surf.get_rect(center=(w // 2, 60)))

        # Player 1 label
        if self._font_medium is not None:
            p1_colour = _TEAM_RED_COLOUR
            p1_label = self._font_medium.render(
                "Player 1 \u2014 Red Army", True, p1_colour
            )
            if is_two_player:
                surface.blit(p1_label, (w // 4 - p1_label.get_width() // 2, 130))
            else:
                surface.blit(p1_label, p1_label.get_rect(center=(w // 2, 130)))

            if is_two_player:
                p2_colour = _TEAM_BLUE_COLOUR
                p2_label = self._font_medium.render(
                    "Player 2 \u2014 Blue Army", True, p2_colour
                )
                surface.blit(p2_label, (3 * w // 4 - p2_label.get_width() // 2, 130))

        # Preview panel — Classic Army info
        preview_rect = _pygame.Rect(w // 2 - 400, 240, 800, 200)
        _pygame.draw.rect(surface, _SURFACE_COLOUR, preview_rect, border_radius=8)
        _pygame.draw.rect(surface, _PANEL_BORDER_COLOUR, preview_rect, 1, border_radius=8)

        if self._font_medium is not None and self._font_small is not None:
            army_name = self._font_medium.render(
                _CLASSIC_ARMY_NAME, True, _TITLE_COLOUR
            )
            surface.blit(army_name, (preview_rect.x + 16, preview_rect.y + 16))
            desc_lines = _CLASSIC_ARMY_DESCRIPTION.split("\n")
            for i, line in enumerate(desc_lines):
                desc_surf = self._font_small.render(line, True, _TEXT_SECONDARY)
                surface.blit(
                    desc_surf,
                    (preview_rect.x + 16, preview_rect.y + 52 + i * 28),
                )
            # Custom army hint
            hint = self._font_small.render(
                "Add custom armies by placing .json files in your army mod folder.",
                True, _TEXT_SECONDARY,
            )
            surface.blit(hint, (preview_rect.x + 16, preview_rect.y + 148))

        # Buttons
        for btn in self._buttons:
            is_hovered = btn["rect"].collidepoint(self._mouse_pos)
            colour = _BTN_HOVER_COLOUR if is_hovered else btn.get("colour", _BTN_COLOUR)
            _pygame.draw.rect(surface, colour, btn["rect"], border_radius=8)
            font = btn.get("font") or self._font_medium
            if font is not None:
                label_surf = font.render(btn["label"], True, _BTN_TEXT_COLOUR)
                surface.blit(label_surf, label_surf.get_rect(center=btn["rect"].center))

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
        """Return the button list for this screen."""
        if _pygame is None:
            return []

        display_info = _pygame.display.Info()
        w = display_info.current_w or 1024
        h = display_info.current_h or 768

        nav_btn_w, nav_btn_h = 160, 48
        nav_y = h - 100
        cx = w // 2

        return [
            {
                "label": "\u2190 Back",
                "rect": _pygame.Rect(cx - nav_btn_w - 20, nav_y, nav_btn_w, nav_btn_h),
                "colour": _BTN_COLOUR,
                "action": self._on_back,
                "font": self._font_medium,
            },
            {
                "label": "Confirm \u2192",
                "rect": _pygame.Rect(cx + 20, nav_y, nav_btn_w, nav_btn_h),
                "colour": _BTN_PRIMARY_COLOUR,
                "action": self._on_confirm,
                "font": self._font_medium,
            },
        ]

    def _on_back(self) -> None:
        """Return to the previous screen (StartGameScreen)."""
        self._screen_manager.pop()

    def _on_confirm(self) -> None:
        """Start a new game session and navigate to the setup screen.

        Delegates to ``game_context.start_new_game()`` which creates the
        ``GameController`` / ``EventBus`` and pushes ``SetupScreen``.
        """
        from src.presentation.screens.start_game_screen import GAME_MODE_VS_AI

        self._game_context.start_new_game(
            game_mode=self._game_mode,
            ai_difficulty=(
                self._ai_difficulty if self._game_mode == GAME_MODE_VS_AI else None
            ),
            screen_manager=self._screen_manager,
        )
