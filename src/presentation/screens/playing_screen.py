"""
src/presentation/screens/playing_screen.py

PlayingScreen — the in-game board screen where players make moves.
Specification: screen_flow.md §3.7
"""
from __future__ import annotations

import logging
from typing import Any

from src.application.event_bus import EventBus
from src.application.events import CombatResolved, GameOver, InvalidMove, PieceMoved, TurnChanged
from src.domain.enums import PlayerSide
from src.domain.game_state import GameState
from src.domain.piece import Position
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
_BOARD_FRACTION: float = 0.75
_BOARD_COLS: int = 10
_BOARD_ROWS: int = 10

# Colour palette
_BG_COLOUR = (20, 30, 48)
_SELECT_COLOUR = (255, 255, 0, 128)  # yellow highlight for selected piece
_INVALID_COLOUR = (255, 80, 80, 128)  # red tint for invalid move flash
_PANEL_COLOUR = (30, 45, 70)
_TEXT_COLOUR = (220, 220, 220)
_BTN_COLOUR = (50, 70, 100)
_BTN_HOVER_COLOUR = (80, 110, 160)
_STATUS_RED = (200, 60, 60)
_STATUS_BLUE = (60, 100, 200)


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
        """
        self._controller = controller
        self._screen_manager = screen_manager
        self._event_bus = event_bus
        self._renderer = renderer
        self._viewing_player = viewing_player

        self._selected_pos: Position | None = None
        self._invalid_flash: float = 0.0   # seconds remaining for red flash
        self._status_message: str = ""
        self._font: Any = None
        self._font_small: Any = None
        self._mouse_pos: tuple[int, int] = (0, 0)
        self._cell_w: int = 0
        self._cell_h: int = 0

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
        self._font = _pygame.font.SysFont("Arial", 24)
        self._font_small = _pygame.font.SysFont("Arial", 18)

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

    def update(self, delta_time: float) -> None:
        """Advance per-frame logic — tick the invalid-move flash timer.

        Args:
            delta_time: Elapsed time since the previous frame, in seconds.
        """
        if self._invalid_flash > 0:
            self._invalid_flash = max(0.0, self._invalid_flash - delta_time)

    # ------------------------------------------------------------------
    # Event handlers (subscribed to EventBus)
    # ------------------------------------------------------------------

    def _on_piece_moved(self, event: PieceMoved) -> None:
        """Handle a successful move — clear selection and update status."""
        self._selected_pos = None
        self._status_message = self._active_player_label()
        logger.debug("PlayingScreen: piece moved %s→%s", event.from_pos, event.to_pos)

    def _on_combat_resolved(self, event: CombatResolved) -> None:
        """Handle combat resolution — update status message."""
        winner_str = (
            str(event.winner.value) if event.winner is not None else "Draw"
        )
        self._status_message = f"Combat: {winner_str} wins!"
        self._selected_pos = None
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
        )
        self._screen_manager.push(game_over_screen)

    def _on_invalid_move(self, event: InvalidMove) -> None:
        """Handle an invalid move — flash the selected square red."""
        self._invalid_flash = 1.5
        self._status_message = f"Invalid: {event.reason}"
        logger.debug("PlayingScreen: invalid move — %s", event.reason)

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
        quit_rect = self._quit_button_rect()
        if quit_rect is not None and quit_rect.collidepoint(pixel_pos):
            self._on_quit_to_menu()

    # ------------------------------------------------------------------
    # Panel rendering helpers
    # ------------------------------------------------------------------

    def _render_panel(self, surface: Any, panel_x: int, panel_w: int, h: int) -> None:
        """Draw the right-hand side panel contents.

        Args:
            surface: Target surface.
            panel_x: X pixel offset where the panel starts.
            panel_w: Width of the panel in pixels.
            h: Height of the window in pixels.
        """
        if _pygame is None or self._font is None:
            return

        cx = panel_x + panel_w // 2

        # Active player label.
        state: GameState = self._controller.current_state
        player_colour = (
            _STATUS_RED if state.active_player == PlayerSide.RED else _STATUS_BLUE
        )
        player_label = self._font.render(
            f"{state.active_player.value}'s turn", True, player_colour
        )
        surface.blit(player_label, player_label.get_rect(center=(cx, 60)))

        # Turn counter.
        if self._font_small is not None:
            turn_label = self._font_small.render(
                f"Turn {state.turn_number}", True, _TEXT_COLOUR
            )
            surface.blit(turn_label, turn_label.get_rect(center=(cx, 100)))

            # Status message.
            if self._status_message:
                status_surf = self._font_small.render(
                    self._status_message, True, _TEXT_COLOUR
                )
                surface.blit(status_surf, status_surf.get_rect(center=(cx, 140)))

        # Quit to Menu button.
        quit_rect = self._quit_button_rect()
        if quit_rect is not None:
            is_hovered = quit_rect.collidepoint(self._mouse_pos)
            btn_colour = _BTN_HOVER_COLOUR if is_hovered else _BTN_COLOUR
            _pygame.draw.rect(surface, btn_colour, quit_rect, border_radius=6)
            if self._font_small is not None:
                quit_label = self._font_small.render("Quit to Menu", True, _TEXT_COLOUR)
                surface.blit(quit_label, quit_label.get_rect(center=quit_rect.center))

    def _quit_button_rect(self) -> Any:
        """Return the pygame.Rect for the 'Quit to Menu' button."""
        if _pygame is None:
            return None
        try:
            info = _pygame.display.Info()
            w = info.current_w or 1024
            h = info.current_h or 768
            panel_x = int(w * _BOARD_FRACTION)
            panel_w = w - panel_x
            cx = panel_x + panel_w // 2
            return _pygame.Rect(cx - 80, h - 80, 160, 40)
        except Exception:
            return None

    def _active_player_label(self) -> str:
        """Return a short status string for the active player."""
        try:
            state: GameState = self._controller.current_state
            return f"{state.active_player.value}'s move"
        except Exception:
            return ""

    def _on_quit_to_menu(self) -> None:
        """Auto-save (future) and return to the main menu."""
        # Pop until MainMenuScreen is reached.  For now we use pop() since
        # PlayingScreen is always on top of SetupScreen which sits on top of
        # StartGameScreen which sits on top of MainMenuScreen.
        # A clean replace(MainMenuScreen) would require a reference to the
        # existing MainMenuScreen instance; use pop-chain for simplicity.
        try:
            # Pop PlayingScreen → SetupScreen (if still in stack)
            self._screen_manager.pop()
        except IndexError:
            pass
