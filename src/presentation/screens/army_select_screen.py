"""
src/presentation/screens/army_select_screen.py

ArmySelectScreen — lets players choose their army variant before setup.
Specification: screen_flow.md §3.3; ux-wireframe-army-select.md
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.domain.classic_army import ClassicArmy
from src.infrastructure.mod_loader import discover_mods
from src.presentation.font_utils import load_font
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

        # Available armies (loaded in on_enter)
        self._available_armies: list[Any] = []
        
        # Selected army mods
        self._player1_army_mod: Any = None
        self._player2_army_mod: Any = None

        # Task notice state (US-807)
        self._show_task_notice_player1: bool = False
        self._show_task_notice_player2: bool = False

        self._font_title: Any = None
        self._font_medium: Any = None
        self._font_small: Any = None
        self._buttons: list[dict[str, Any]] = []
        self._mouse_pos: tuple[int, int] = (0, 0)
        
        # Active selector for keyboard input (0 = Player 1, 1 = Player 2/AI)
        self._active_selector: int = 0

    # ------------------------------------------------------------------
    # Public accessors (used by tests)
    # ------------------------------------------------------------------

    @property
    def player1_army(self) -> str:
        """Selected army name for Player 1."""
        return self._player1_army_mod.army_name if self._player1_army_mod else _CLASSIC_ARMY_NAME

    @property
    def player2_army(self) -> str:
        """Selected army name for Player 2 (may equal Player 1 in 2-player mode)."""
        return self._player2_army_mod.army_name if self._player2_army_mod else _CLASSIC_ARMY_NAME

    @property
    def player1_army_mod(self) -> Any:
        """Selected ArmyMod for Player 1."""
        return self._player1_army_mod

    @property
    def player2_army_mod(self) -> Any:
        """Selected ArmyMod for Player 2."""
        return self._player2_army_mod
        """True when Player 1's selected army has at least one unit with tasks (US-807)."""
        return self._show_task_notice_player1

    @property
    def show_task_notice_player2(self) -> bool:
        """True when Player 2's selected army has at least one unit with tasks (US-807)."""
        return self._show_task_notice_player2

    @property
    def task_notice_text(self) -> str:
        """Text shown in the preview panel when an army includes unit tasks (US-807)."""
        return "\u2139 This army includes unit tasks"

    @property
    def task_notice_tooltip(self) -> str:
        """Tooltip explaining the task notice (US-807 AC-3)."""
        return (
            "When a unit with tasks captures an enemy piece, you will be asked "
            "to complete a physical exercise before the game continues."
        )

    def select_army(self, player: int, army_mod: Any) -> None:
        """Update the selected army for *player* and refresh the task notice.

        Args:
            player: ``1`` for Player 1, ``2`` for Player 2.
            army_mod: An :class:`~src.domain.army_mod.ArmyMod` instance (or
                a duck-typed equivalent) to inspect for task configuration.
        """
        has_tasks = any(
            len(getattr(uc, "tasks", [])) > 0
            for uc in getattr(army_mod, "unit_customisations", {}).values()
        )
        if player == 1:
            self._player1_army_mod = army_mod
            self._show_task_notice_player1 = has_tasks
        elif player == 2:
            self._player2_army_mod = army_mod
            self._show_task_notice_player2 = has_tasks


    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, data: dict[str, Any]) -> None:
        """Initialise fonts, load available armies, and build the button layout.

        Args:
            data: Context data from ``StartGameScreen.on_exit()``.
                  May contain ``game_mode`` and ``ai_difficulty`` overrides.
        """
        if "game_mode" in data:
            self._game_mode = data["game_mode"]
        if "ai_difficulty" in data:
            self._ai_difficulty = data["ai_difficulty"]

        # Load available armies
        self._available_armies = [ClassicArmy.get()]
        mod_dir = Path("mods")
        if mod_dir.exists():
            self._available_armies.extend(discover_mods(mod_dir))
        
        # Set default selections to Classic Army
        classic_army = self._available_armies[0]
        self._player1_army_mod = classic_army
        self._player2_army_mod = classic_army

        if _pygame is None:
            return
        if not _pygame.get_init():
            _pygame.init()
        _pygame.font.init()
        self._font_title = load_font(_pygame.font, 44, bold=True)
        self._font_medium = load_font(_pygame.font, 28)
        self._font_small = load_font(_pygame.font, 18)
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
            "player1_army": self._player1_army_mod,
            "player2_army": self._player2_army_mod,
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
        title_text = "Choose Your Armies"  # Always plural now
        if self._font_title is not None:
            title_surf = self._font_title.render(title_text, True, _TITLE_COLOUR)
            surface.blit(title_surf, title_surf.get_rect(center=(w // 2, 60)))

        # Player 1 label
        if self._font_medium is not None:
            p1_colour = _TEAM_RED_COLOUR
            p1_label = self._font_medium.render(
                "Player 1 \u2014 Red Army", True, p1_colour
            )
            if self._game_mode == "TWO_PLAYER":
                surface.blit(p1_label, (w // 4 - p1_label.get_width() // 2, 130))
            else:  # VS_AI mode
                surface.blit(p1_label, (w // 4 - p1_label.get_width() // 2, 130))

            if self._game_mode == "TWO_PLAYER":
                p2_colour = _TEAM_BLUE_COLOUR
                p2_label = self._font_medium.render(
                    "Player 2 \u2014 Blue Army", True, p2_colour
                )
                surface.blit(p2_label, (3 * w // 4 - p2_label.get_width() // 2, 130))
            else:  # VS_AI mode
                ai_colour = _TEAM_BLUE_COLOUR
                ai_label = self._font_medium.render(
                    "AI \u2014 Blue Army", True, ai_colour
                )
                surface.blit(ai_label, (3 * w // 4 - ai_label.get_width() // 2, 130))

        # Preview panel — Classic Army info
        preview_rect = _pygame.Rect(w // 2 - 400, 240, 800, 200)
        _pygame.draw.rect(surface, _SURFACE_COLOUR, preview_rect, border_radius=8)
        _pygame.draw.rect(surface, _PANEL_BORDER_COLOUR, preview_rect, 1, border_radius=8)

        if self._font_medium is not None and self._font_small is not None:
            # Show the army of the active selector
            if self._active_selector == 0:
                current_army = self._player1_army_mod
                selector_name = "Player 1"
            else:
                current_army = self._player2_army_mod
                selector_name = "Player 2" if self._game_mode == "TWO_PLAYER" else "AI"
            
            army_label = current_army.army_name if current_army else _CLASSIC_ARMY_NAME
            army_name = self._font_medium.render(
                f"{selector_name}: {army_label}", True, _TITLE_COLOUR
            )
            surface.blit(army_name, (preview_rect.x + 16, preview_rect.y + 16))
            
            # Description
            description = getattr(current_army, 'description', None) if current_army else None
            if description:
                desc_lines = description.split("\n")
            else:
                desc_lines = _CLASSIC_ARMY_DESCRIPTION.split("\n")
            
            for i, line in enumerate(desc_lines):
                desc_surf = self._font_small.render(line, True, _TEXT_SECONDARY)
                surface.blit(
                    desc_surf,
                    (preview_rect.x + 16, preview_rect.y + 52 + i * 28),
                )
            
            # Custom army hint
            if len(self._available_armies) > 1:
                hint = self._font_small.render(
                    f"Tab to switch selector, arrow keys to cycle through"
                    f" {len(self._available_armies)} armies.",
                    True, _TEXT_SECONDARY,
                )
            else:
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

        # Keyboard shortcuts for army selection (temporary until proper UI is implemented)
        if event.type == _pygame.KEYDOWN:
            if event.key == _pygame.K_TAB:
                # Switch active selector
                num_selectors = 2  # Always 2 in current implementation
                self._active_selector = (self._active_selector + 1) % num_selectors
            elif event.key == _pygame.K_LEFT or event.key == _pygame.K_UP:
                self._cycle_army(-1)
            elif event.key == _pygame.K_RIGHT or event.key == _pygame.K_DOWN:
                self._cycle_army(1)

    def _cycle_army(self, direction: int) -> None:
        """Cycle through available armies for the active selector.
        
        Args:
            direction: +1 for next army, -1 for previous army
        """
        if not self._available_armies:
            return
        
        # Determine which army mod to cycle
        if self._active_selector == 0:
            current_army = self._player1_army_mod
        else:
            current_army = self._player2_army_mod
        
        current_index = 0
        for i, army in enumerate(self._available_armies):
            if army.army_name == current_army.army_name:
                current_index = i
                break
        
        new_index = (current_index + direction) % len(self._available_armies)
        new_army = self._available_armies[new_index]
        
        player_num = self._active_selector + 1
        self.select_army(player_num, new_army)

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
            player1_army=self._player1_army_mod,
            player2_army=self._player2_army_mod,
        )
