"""
src/presentation/screens/playing_screen.py

PlayingScreen — the in-game board screen where players make moves.
Specification: screen_flow.md §3.7
"""
from __future__ import annotations

import logging
import random
from typing import Any

from src.application.event_bus import EventBus
from src.application.events import (
    CombatResolved,
    GameOver,
    GameSaved,
    InvalidMove,
    PieceMoved,
    TurnChanged,
)
from src.domain.enums import PlayerSide, PlayerType, Rank
from src.domain.game_state import GameState
from src.domain.piece import Position
from src.presentation.font_utils import load_font
from src.presentation.screens.base import Screen

logger = logging.getLogger(__name__)

# Lazy import of pygame so the module works in headless test environments.
try:
    import pygame as _pygame

    _QUIT = _pygame.QUIT
    _MOUSEBUTTONDOWN = _pygame.MOUSEBUTTONDOWN
    _MOUSEMOTION = _pygame.MOUSEMOTION
except ImportError:
    _pygame = None  # type: ignore[assignment]
    _QUIT = 256
    _MOUSEBUTTONDOWN = 1025
    _MOUSEMOTION = 1024

# Layout constants — must match pygame_renderer.py
_BOARD_FRACTION: float = 0.80
_BOARD_COLS: int = 10
_BOARD_ROWS: int = 10

# Colour palette
_BG_COLOUR = (20, 30, 48)
_SELECT_COLOUR = (255, 255, 0, 128)  # yellow highlight for selected piece
_INVALID_COLOUR = (255, 80, 80, 128)  # red tint for invalid move flash
_PANEL_COLOUR = (30, 45, 70)
_PANEL_BORDER_COLOUR = (60, 80, 110)
_TEXT_COLOUR = (220, 220, 220)
_TEXT_SECONDARY = (150, 160, 180)
_BTN_COLOUR = (50, 70, 100)
_BTN_HOVER_COLOUR = (80, 110, 160)
_BTN_DANGER_COLOUR = (120, 40, 40)
_BTN_DANGER_HOVER_COLOUR = (180, 60, 60)
_STATUS_RED = (200, 60, 60)
_STATUS_BLUE = (60, 100, 200)

# Re-highlight colours for post-popup dismissal (US-808)
_COLOUR_MOVE_LAST_FROM = (230, 126, 34)   # #E67E22
_COLOUR_MOVE_LAST_TO = (243, 156, 18)     # #F39C12
_REHIGHLIGHT_DURATION_MS = 2000           # milliseconds

# Friendly player names (H1.4).
_PLAYER_NAMES: dict[PlayerSide, str] = {
    PlayerSide.RED: "Red Army",
    PlayerSide.BLUE: "Blue Army",
}

# Human-readable invalid-move messages (H9.1).
_INVALID_MOVE_MESSAGES: dict[str, str] = {
    "piece_blocked": "That path is blocked",
    "wrong_turn": "It is not your turn",
    "immovable_piece": "Bombs and Flags cannot move",
    "out_of_bounds": "That square is off the board",
    "lake_square": "Pieces cannot enter the lake",
    "friendly_fire": "You cannot capture your own piece",
    "two_square_rule": (
        "You cannot move this piece back and forth on consecutive turns "
        "(two-square rule)"
    ),
    "no_piece": "No piece at that position",
    "wrong_phase": "Moves are not allowed during setup",
}

# Rank abbreviations used in the captured-pieces tray (wireframe §4).
_RANK_ABBREV: dict[Rank, str] = {
    Rank.MARSHAL: "Ma",
    Rank.GENERAL: "Ge",
    Rank.COLONEL: "Co",
    Rank.MAJOR: "Mj",
    Rank.CAPTAIN: "Ca",
    Rank.LIEUTENANT: "Li",
    Rank.SERGEANT: "Se",
    Rank.MINER: "Mi",
    Rank.SCOUT: "Sc",
    Rank.SPY: "Sp",
    Rank.BOMB: "Bm",
    Rank.FLAG: "Fl",
}


class PlayingScreen(Screen):
    """The main in-game screen — renders the board and handles player input.

    Subscribes to domain events from the ``EventBus`` and re-renders
    reactively.  The first mouse click selects a friendly piece; the second
    click on a valid square submits a ``MovePiece`` command via the
    ``GameController``.  A right-click deselects the current piece.

    Specification: screen_flow.md §3.7
    """

    def __init__(
        self,
        controller: Any,
        screen_manager: Any,
        event_bus: EventBus,
        renderer: Any,
        viewing_player: PlayerSide = PlayerSide.RED,
        game_context: Any = None,
        undo_enabled: bool = False,
    ) -> None:
        """Initialise the playing screen.

        Args:
            controller: The ``GameController`` that processes ``MovePiece``
                commands.
            screen_manager: The ``ScreenManager`` for navigation.
            event_bus: The shared ``EventBus`` for domain events.
            renderer: An adapter with a ``render(state)`` method that draws
                the board and flips the display buffer.
            viewing_player: The player whose perspective is shown
                (fog-of-war).  Defaults to ``PlayerSide.RED``.
            game_context: Optional ``_GameContext`` — forwarded to
                ``GameOverScreen`` to enable proper navigation from the
                game-over screen.
            undo_enabled: Whether the Undo button should be shown in the
                side panel.  Defaults to ``False``.
        """
        self._controller = controller
        self._screen_manager = screen_manager
        self._event_bus = event_bus
        self._renderer = renderer
        self._viewing_player = viewing_player
        self._game_context = game_context
        self._undo_enabled = undo_enabled

        self._selected_pos: Position | None = None
        self._invalid_flash: float = 0.0   # seconds remaining for red flash
        self._status_message: str = ""
        self._last_move_text: str = ""       # last-move summary for side panel
        self._captured_by_red: list[str] = []    # rank abbrevs captured by RED
        self._captured_by_blue: list[str] = []   # rank abbrevs captured by BLUE
        self._font: Any = None
        self._font_small: Any = None
        self._mouse_pos: tuple[int, int] = (0, 0)
        self._cell_w: int = 0
        self._cell_h: int = 0

        # Task popup state (US-804)
        self.popup_active: bool = False
        self._popup: Any = None
        self._active_task: Any = None

        # Re-highlight state (US-808)
        self.post_popup_rehighlight_timer: int = 0
        self.rehighlight_from_colour: tuple[int, int, int] = _COLOUR_MOVE_LAST_FROM
        self.rehighlight_to_colour: tuple[int, int, int] = _COLOUR_MOVE_LAST_TO
        self._rehighlight_from_pos: Position | None = None
        self._rehighlight_to_pos: Position | None = None

        # Subscribe to domain events.
        event_bus.subscribe(PieceMoved, self._on_piece_moved)
        event_bus.subscribe(CombatResolved, self._on_combat_resolved)
        event_bus.subscribe(TurnChanged, self._on_turn_changed)
        event_bus.subscribe(GameOver, self._on_game_over)
        event_bus.subscribe(InvalidMove, self._on_invalid_move)

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, data: dict[str, Any]) -> None:
        """Initialise fonts and layout geometry.

        Args:
            data: May contain ``viewing_player`` to override the default.
        """
        if "viewing_player" in data:
            self._viewing_player = data["viewing_player"]

        if _pygame is None:
            return
        if not _pygame.get_init():
            _pygame.init()
        _pygame.font.init()
        self._font = load_font(_pygame.font, 24)
        self._font_small = load_font(_pygame.font, 18)

        # Cache cell dimensions from the current display.
        try:
            info = _pygame.display.Info()
            w = info.current_w or 1024
            h = info.current_h or 768
            board_w = int(w * _BOARD_FRACTION)
            self._cell_w = board_w // _BOARD_COLS
            self._cell_h = h // _BOARD_ROWS
        except Exception:
            self._cell_w = 76
            self._cell_h = 76

        self._status_message = self._active_player_label()

    def on_exit(self) -> dict[str, Any]:
        """Return the final game state when leaving this screen.

        Returns:
            A dict containing the ``GameController``'s current state.
        """
        return {"game_state": self._controller.current_state}

    def render(self, surface: Any) -> None:
        """Render the board and side panel onto *surface*.

        The board is drawn by the injected *renderer*.  The side panel
        (right 25 % of the window) shows the active player and status
        messages.

        Args:
            surface: The target ``pygame.Surface`` (may be ``None`` in
                headless mode).
        """
        if surface is None or _pygame is None:
            return

        # Board area — delegate to the existing renderer.
        self._renderer.render(self._controller.current_state)

        w: int = surface.get_width()
        h: int = surface.get_height()
        panel_x = int(w * _BOARD_FRACTION)
        panel_w = w - panel_x

        # Side panel background.
        _pygame.draw.rect(surface, _PANEL_COLOUR, (panel_x, 0, panel_w, h))

        # Selected-piece highlight overlay.
        if self._selected_pos is not None and self._cell_w and self._cell_h:
            highlight = _pygame.Surface((self._cell_w, self._cell_h), _pygame.SRCALPHA)
            highlight.fill(_SELECT_COLOUR)
            x = self._selected_pos.col * self._cell_w
            y = self._selected_pos.row * self._cell_h
            surface.blit(highlight, (x, y))

        # Invalid-move flash overlay.
        if self._invalid_flash > 0 and self._selected_pos is not None:
            flash = _pygame.Surface((self._cell_w, self._cell_h), _pygame.SRCALPHA)
            flash.fill(_INVALID_COLOUR)
            x = self._selected_pos.col * self._cell_w
            y = self._selected_pos.row * self._cell_h
            surface.blit(flash, (x, y))

        if self._font is not None and self._font_small is not None:
            self._render_panel(surface, panel_x, panel_w, h)

    def handle_event(self, event: Any) -> None:
        """Process a single input event.

        Args:
            event: A pygame event (or ``None`` in headless mode).
        """
        if event is None or _pygame is None:
            return

        if event.type == _MOUSEMOTION:
            self._mouse_pos = event.pos
            return

        if event.type == _QUIT:
            _pygame.event.post(_pygame.event.Event(_pygame.QUIT))
            return

        if event.type == _MOUSEBUTTONDOWN:
            if event.button == 3:
                # Right-click deselects.
                self._selected_pos = None
                return
            if event.button == 1:
                self._handle_left_click(event.pos)

    def update(self, delta_time: float = 0.0, *, delta_time_ms: float | None = None) -> None:
        """Advance per-frame logic — tick the invalid-move flash and re-highlight timers.

        Args:
            delta_time: Elapsed time since the previous frame, in seconds.
                Used for the invalid-move flash (existing behaviour).
            delta_time_ms: Elapsed time in milliseconds (keyword-only).
                When provided, *delta_time* is ignored for the flash timer and
                both timers are driven by the ms value.
        """
        if delta_time_ms is not None:
            dt_seconds = delta_time_ms / 1000.0
            dt_ms = int(delta_time_ms)
        else:
            dt_seconds = delta_time
            dt_ms = int(delta_time * 1000.0)

        if self._invalid_flash > 0:
            self._invalid_flash = max(0.0, self._invalid_flash - dt_seconds)

        if self.post_popup_rehighlight_timer > 0:
            self.post_popup_rehighlight_timer = max(
                0, self.post_popup_rehighlight_timer - dt_ms
            )

    # ------------------------------------------------------------------
    # Event handlers (subscribed to EventBus)
    # ------------------------------------------------------------------

    def _on_piece_moved(self, event: PieceMoved) -> None:
        """Handle a successful move — clear selection and update status."""
        self._selected_pos = None
        owner = event.piece.owner.value.upper()
        fr = event.from_pos
        to = event.to_pos
        # Convert zero-based indices to algebraic notation (col letter + row number).
        col_letters = "ABCDEFGHIJ"
        fr_cell = f"{col_letters[fr.col]}{10 - fr.row}"
        to_cell = f"{col_letters[to.col]}{10 - to.row}"
        self._last_move_text = f"{owner} {fr_cell}→{to_cell}"
        self._status_message = self._active_player_label()
        logger.debug("PlayingScreen: piece moved %s→%s", event.from_pos, event.to_pos)

    def _on_combat_resolved(self, event: CombatResolved) -> None:
        """Handle combat resolution — update status, captured-pieces tray, and task popup."""
        winner_str = (
            str(event.winner.value) if event.winner is not None else "Draw"
        )
        self._status_message = f"Combat: {winner_str} wins!"
        self._selected_pos = None

        # Track captured pieces for the side-panel tray.
        if event.winner == PlayerSide.RED:
            # RED wins combat → RED captured a BLUE piece (the defender).
            abbrev = _RANK_ABBREV.get(event.defender.rank, "?")
            self._captured_by_red.append(abbrev)
        elif event.winner == PlayerSide.BLUE:
            # BLUE wins combat → BLUE captured a RED piece (the attacker).
            abbrev = _RANK_ABBREV.get(event.attacker.rank, "?")
            self._captured_by_blue.append(abbrev)

        # Task popup trigger (US-804)
        self._maybe_show_task_popup(event)

        logger.debug("PlayingScreen: combat resolved, winner=%s", event.winner)

    def _on_turn_changed(self, event: TurnChanged) -> None:
        """Handle a turn change — update the active-player indicator."""
        self._status_message = self._active_player_label()
        self._selected_pos = None

    def _on_game_over(self, event: GameOver) -> None:
        """Handle game over — push the game over screen."""
        logger.info("PlayingScreen: game over — winner=%s reason=%s", event.winner, event.reason)
        from src.presentation.screens.game_over_screen import GameOverScreen

        game_over_screen = GameOverScreen(
            screen_manager=self._screen_manager,
            winner=event.winner,
            reason=event.reason,
            turn_count=self._controller.current_state.turn_number,
            game_context=self._game_context,
        )
        self._screen_manager.push(game_over_screen)

    def _on_invalid_move(self, event: InvalidMove) -> None:
        """Handle an invalid move — flash the selected square red."""
        self._invalid_flash = 1.5
        friendly_msg = _INVALID_MOVE_MESSAGES.get(event.reason, event.reason)
        self._status_message = friendly_msg
        logger.debug("PlayingScreen: invalid move — %s", event.reason)

    # ------------------------------------------------------------------
    # Task popup helpers (US-804, US-808)
    # ------------------------------------------------------------------

    def _get_unit_customisation(self, rank: Rank) -> Any:
        """Return the :class:`~src.domain.army_mod.UnitCustomisation` for *rank*.

        The default implementation returns ``None`` (no custom army is loaded).
        Tests patch this method to return specific customisation objects without
        requiring a real army mod to be loaded.

        Args:
            rank: The :class:`~src.domain.enums.Rank` to look up.

        Returns:
            A :class:`~src.domain.army_mod.UnitCustomisation` instance, or
            ``None`` if no customisation is available.
        """
        return None

    def _maybe_show_task_popup(self, event: CombatResolved) -> None:
        """Conditionally show the task popup after combat resolution (US-804).

        Trigger conditions (all must be true):
        1. There is a winner (not a draw).
        2. The captured player is of type ``PlayerType.HUMAN``.
        3. The capturing unit's :class:`~src.domain.army_mod.UnitCustomisation`
           has at least one task configured.

        Args:
            event: The resolved :class:`~src.application.events.CombatResolved` event.
        """
        if event.winner is None:
            return  # Draw — no capture

        # Identify the capturing and captured pieces.
        if event.winner == event.attacker.owner:
            capturing_piece = event.attacker
            captured_piece = event.defender
        else:
            capturing_piece = event.defender
            captured_piece = event.attacker

        # Check that the captured player is human.
        state = self._controller.current_state
        captured_side = captured_piece.owner
        try:
            captured_player = state.players.get(captured_side)
        except AttributeError:
            return

        if captured_player is None:
            return
        if getattr(captured_player, "player_type", None) != PlayerType.HUMAN:
            return  # AI captured — no popup

        # Check that the capturing unit has tasks configured.
        customisation = self._get_unit_customisation(capturing_piece.rank)
        tasks = getattr(customisation, "tasks", [])
        if not tasks:
            return  # No tasks — no popup

        # Select one task at random (US-804 AC-7).
        task = random.choice(tasks)  # noqa: S311
        self._active_task = task
        self.popup_active = True

        logger.debug(
            "PlayingScreen: task popup triggered for rank=%s task='%s'",
            capturing_piece.rank,
            task.description,
        )

    def dismiss_popup(self) -> None:
        """Dismiss the active task popup and start the re-highlight timer (US-808).

        Called by the popup's ``on_dismiss`` callback or directly by tests.
        After dismissal:
        - ``popup_active`` is set to ``False``.
        - ``post_popup_rehighlight_timer`` is reset to 2000 ms.
        - Normal board input is restored.
        """
        self.popup_active = False
        self._popup = None
        self.post_popup_rehighlight_timer = _REHIGHLIGHT_DURATION_MS
        logger.debug("PlayingScreen: task popup dismissed; rehighlight timer started.")

    def cancel_rehighlight(self) -> None:
        """Cancel the post-popup re-highlight timer (US-808 AC-4).

        Called when the player starts a new move before the 2-second timer
        expires, so that the new move's highlights replace the re-highlight.
        """
        self.post_popup_rehighlight_timer = 0

    # ------------------------------------------------------------------
    # Click handling
    # ------------------------------------------------------------------

    def _handle_left_click(self, pixel_pos: tuple[int, int]) -> None:
        """Convert a pixel left-click to a board action.

        First click on a friendly piece: select it.
        Second click on any square: attempt to move the selected piece there.
        Clicking outside the board area activates the side-panel buttons.

        Args:
            pixel_pos: The (x, y) pixel coordinates of the click.
        """
        px, py = pixel_pos
        if self._cell_w == 0 or self._cell_h == 0:
            return

        board_pixel_w = self._cell_w * _BOARD_COLS
        if px >= board_pixel_w:
            # Click is in the side panel — handle panel buttons.
            self._handle_panel_click(pixel_pos)
            return

        col = min(px // self._cell_w, _BOARD_COLS - 1)
        row = min(py // self._cell_h, _BOARD_ROWS - 1)
        clicked_pos = Position(row, col)

        state: GameState = self._controller.current_state

        if self._selected_pos is None:
            # Select a piece if it belongs to the active player.
            sq = state.board.get_square(clicked_pos)
            if sq.piece is not None and sq.piece.owner == state.active_player:
                self._selected_pos = clicked_pos
        else:
            if clicked_pos == self._selected_pos:
                # Click same square → deselect.
                self._selected_pos = None
            else:
                # Attempt to move the selected piece.
                from src.application.commands import MovePiece

                cmd = MovePiece(
                    from_pos=self._selected_pos,
                    to_pos=clicked_pos,
                )
                self._controller.submit_command(cmd)
                # Selection is cleared by _on_piece_moved or _on_invalid_move
                # callbacks via the event bus.

    def _handle_panel_click(self, pixel_pos: tuple[int, int]) -> None:
        """Handle clicks in the right-hand side panel (e.g. Quit to Menu).

        Args:
            pixel_pos: The (x, y) pixel coordinates of the click.
        """
        if _pygame is None:
            return
        save_rect = self._save_button_rect()
        if save_rect is not None and save_rect.collidepoint(pixel_pos):
            self._on_save_game()
            return
        undo_rect = self._undo_button_rect()
        if undo_rect is not None and undo_rect.collidepoint(pixel_pos):
            self._on_undo()
            return
        quit_rect = self._quit_button_rect()
        if quit_rect is not None and quit_rect.collidepoint(pixel_pos):
            self._on_quit_to_menu()

    # ------------------------------------------------------------------
    # Panel rendering helpers
    # ------------------------------------------------------------------

    def _render_panel(self, surface: Any, panel_x: int, panel_w: int, h: int) -> None:
        """Draw the right-hand side panel contents per the wireframe layout.

        Sections (top → bottom):
        1. Player label (♦/♠ indicator + army name + turn indicator)
        2. Turn counter
        3. Separator
        4. Status / last-move summary
        5. Separator
        6. Captured pieces tray (by RED / by BLUE)
        7. Separator
        8. Save Game button
        9. Undo button (if ``undo_enabled``)
        10. Separator
        11. Quit to Menu button

        Args:
            surface: Target surface.
            panel_x: X pixel offset where the panel starts.
            panel_w: Width of the panel in pixels.
            h: Height of the window in pixels.
        """
        if _pygame is None or self._font is None or self._font_small is None:
            return

        pad = 10  # left/right padding inside panel
        left = panel_x + pad
        y = 14  # running y cursor

        state: GameState = self._controller.current_state
        is_red = state.active_player == PlayerSide.RED
        player_colour = _STATUS_RED if is_red else _STATUS_BLUE
        player_name = _PLAYER_NAMES.get(state.active_player, state.active_player.value)

        # --- Section 1: Player label ------------------------------------------
        # Draw ♦ / ♠ indicator dot (10 px radius) left-aligned.
        indicator_symbol = "♦" if is_red else "♠"
        indicator_surf = self._font.render(indicator_symbol, True, player_colour)
        surface.blit(indicator_surf, (left, y))
        # Army name right of the indicator.
        name_surf = self._font.render(player_name.upper(), True, player_colour)
        surface.blit(name_surf, (left + indicator_surf.get_width() + 6, y))
        y += name_surf.get_height() + 4

        # Active-turn indicator bullet.
        if state.active_player == self._viewing_player:
            turn_indicator = "● Your turn"
        else:
            turn_indicator = "○ Opponent's turn"
        turn_ind_surf = self._font_small.render(turn_indicator, True, player_colour)
        surface.blit(turn_ind_surf, (left, y))
        y += turn_ind_surf.get_height() + 4

        # Turn counter.
        turn_surf = self._font_small.render(
            f"Turn {state.turn_number}", True, _TEXT_SECONDARY
        )
        surface.blit(turn_surf, (left, y))
        y += turn_surf.get_height() + 8

        # --- Separator --------------------------------------------------------
        sep_x_end = panel_x + panel_w - pad
        _pygame.draw.line(surface, _PANEL_BORDER_COLOUR, (panel_x + pad, y), (sep_x_end, y))
        y += 10

        # --- Section 2: Status / last-move summary ----------------------------
        if self._last_move_text or self._status_message:
            move_header = self._font_small.render("Last move:", True, _TEXT_SECONDARY)
            surface.blit(move_header, (left, y))
            y += move_header.get_height() + 2
            body_text = self._last_move_text or self._status_message
            move_surf = self._font_small.render(body_text, True, _TEXT_COLOUR)
            surface.blit(move_surf, (left, y))
            y += move_surf.get_height() + 4

        # Status message (shown separately when it differs from last move).
        if self._status_message and self._status_message != self._last_move_text:
            status_surf = self._font_small.render(self._status_message, True, _TEXT_COLOUR)
            surface.blit(status_surf, (left, y))
            y += status_surf.get_height() + 4

        y += 4

        # --- Separator --------------------------------------------------------
        _pygame.draw.line(surface, _PANEL_BORDER_COLOUR, (panel_x + pad, y), (sep_x_end, y))
        y += 10

        # --- Section 3: Captured pieces tray ----------------------------------
        cap_header_red = self._font_small.render("Captured by RED:", True, _STATUS_RED)
        surface.blit(cap_header_red, (left, y))
        y += cap_header_red.get_height() + 2
        cap_text = " ".join(self._captured_by_red) if self._captured_by_red else "—"
        cap_red_surf = self._font_small.render(cap_text, True, _TEXT_COLOUR)
        surface.blit(cap_red_surf, (left, y))
        y += cap_red_surf.get_height() + 6

        cap_header_blue = self._font_small.render("Captured by BLUE:", True, _STATUS_BLUE)
        surface.blit(cap_header_blue, (left, y))
        y += cap_header_blue.get_height() + 2
        cap_text_b = " ".join(self._captured_by_blue) if self._captured_by_blue else "—"
        cap_blue_surf = self._font_small.render(cap_text_b, True, _TEXT_COLOUR)
        surface.blit(cap_blue_surf, (left, y))
        y += cap_blue_surf.get_height() + 8

        # --- Separator --------------------------------------------------------
        _pygame.draw.line(surface, _PANEL_BORDER_COLOUR, (panel_x + pad, y), (sep_x_end, y))

        # --- Section 4: Buttons (anchored near bottom) ------------------------
        btn_h = 38
        btn_w = panel_w - pad * 2
        btn_x = panel_x + pad

        # Calculate button positions from the bottom up.
        quit_rect = _pygame.Rect(btn_x, h - btn_h - 10, btn_w, btn_h)
        buttons: list[tuple[Any, str, bool]] = []  # (rect, label, is_danger)

        if self._undo_enabled:
            undo_rect = _pygame.Rect(btn_x, quit_rect.top - btn_h - 8, btn_w, btn_h)
            save_rect = _pygame.Rect(btn_x, undo_rect.top - btn_h - 8, btn_w, btn_h)
            buttons = [
                (save_rect, "\U0001f4be Save", False),
                (undo_rect, "\u21a9 Undo", False),
                (quit_rect, "Quit \u2715", True),
            ]
        else:
            save_rect = _pygame.Rect(btn_x, quit_rect.top - btn_h - 8, btn_w, btn_h)
            buttons = [
                (save_rect, "\U0001f4be Save", False),
                (quit_rect, "Quit \u2715", True),
            ]

        for rect, label, is_danger in buttons:
            hovered = rect.collidepoint(self._mouse_pos)
            if is_danger:
                colour = _BTN_DANGER_HOVER_COLOUR if hovered else _BTN_DANGER_COLOUR
            else:
                colour = _BTN_HOVER_COLOUR if hovered else _BTN_COLOUR
            _pygame.draw.rect(surface, colour, rect, border_radius=6)
            lbl_surf = self._font_small.render(label, True, _TEXT_COLOUR)
            surface.blit(lbl_surf, lbl_surf.get_rect(center=rect.center))

    def _save_button_rect(self) -> Any:
        """Return the pygame.Rect for the 'Save' button."""
        if _pygame is None:
            return None
        try:
            surface = _pygame.display.get_surface()
            if surface is not None:
                w = surface.get_width()
                h = surface.get_height()
            else:
                info = _pygame.display.Info()
                w = info.current_w or 1024
                h = info.current_h or 768
            panel_x = int(w * _BOARD_FRACTION)
            panel_w = w - panel_x
            pad = 10
            btn_h = 38
            btn_w = panel_w - pad * 2
            btn_x = panel_x + pad
            quit_top = h - btn_h - 10
            if self._undo_enabled:
                undo_top = quit_top - btn_h - 8
                save_top = undo_top - btn_h - 8
            else:
                save_top = quit_top - btn_h - 8
            return _pygame.Rect(btn_x, save_top, btn_w, btn_h)
        except Exception:
            return None

    def _undo_button_rect(self) -> Any:
        """Return the pygame.Rect for the 'Undo' button, or ``None`` if disabled."""
        if _pygame is None or not self._undo_enabled:
            return None
        try:
            surface = _pygame.display.get_surface()
            if surface is not None:
                w = surface.get_width()
                h = surface.get_height()
            else:
                info = _pygame.display.Info()
                w = info.current_w or 1024
                h = info.current_h or 768
            panel_x = int(w * _BOARD_FRACTION)
            panel_w = w - panel_x
            pad = 10
            btn_h = 38
            btn_w = panel_w - pad * 2
            btn_x = panel_x + pad
            quit_top = h - btn_h - 10
            undo_top = quit_top - btn_h - 8
            return _pygame.Rect(btn_x, undo_top, btn_w, btn_h)
        except Exception:
            return None

    def _quit_button_rect(self) -> Any:
        """Return the pygame.Rect for the 'Quit to Menu' button."""
        if _pygame is None:
            return None
        try:
            surface = _pygame.display.get_surface()
            if surface is not None:
                w = surface.get_width()
                h = surface.get_height()
            else:
                info = _pygame.display.Info()
                w = info.current_w or 1024
                h = info.current_h or 768
            panel_x = int(w * _BOARD_FRACTION)
            panel_w = w - panel_x
            pad = 10
            btn_h = 38
            btn_w = panel_w - pad * 2
            btn_x = panel_x + pad
            return _pygame.Rect(btn_x, h - btn_h - 10, btn_w, btn_h)
        except Exception:
            return None

    def _active_player_label(self) -> str:
        """Return a short status string for the active player (H1.4)."""
        try:
            state: GameState = self._controller.current_state
            name = _PLAYER_NAMES.get(state.active_player, state.active_player.value)
            return f"{name}'s move"
        except Exception:
            return ""

    def _on_save_game(self) -> None:
        """Save the current game state to the repository."""
        try:
            if self._game_context is not None and hasattr(self._game_context, "repository"):
                state = self._controller.current_state
                filename = f"save_turn{state.turn_number}.json"
                saved_path = self._game_context.repository.save(state, filename)
                self._event_bus.publish(GameSaved(filepath=str(saved_path)))
                self._status_message = "Game saved!"
        except Exception:  # noqa: BLE001
            self._status_message = "Save failed"

    def _on_undo(self) -> None:
        """Undo the last move if undo is enabled."""
        if not self._undo_enabled:
            return
        try:
            if hasattr(self._controller, "undo"):
                self._controller.undo()
                self._status_message = "Move undone"
                # Roll back the last-move text and captured tray entry.
                self._last_move_text = ""
        except Exception:  # noqa: BLE001
            self._status_message = "Cannot undo"

    def _on_quit_to_menu(self) -> None:
        """Auto-save (future) and return to the main menu.

        Pops all game screens until only the root ``MainMenuScreen`` remains,
        so the playing screen is not left on the stack (H3.3).
        """
        # Pop every screen except the root (base) screen.
        while len(self._screen_manager.stack) > 1:
            try:
                self._screen_manager.pop()
            except IndexError:
                break
