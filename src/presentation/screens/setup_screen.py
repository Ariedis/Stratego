"""
src/presentation/screens/setup_screen.py

SetupScreen — piece placement UI for the Stratego setup phase.
Specification: screen_flow.md §3.6; system_design.md §2.4
"""
from __future__ import annotations

import random
from dataclasses import replace as dc_replace
from typing import Any

from src.application.commands import PlacePiece
from src.application.event_bus import EventBus
from src.domain.enums import GamePhase, PlayerSide, PlayerType, Rank
from src.domain.piece import Piece, Position
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

# Colour palette
_BG_COLOUR = (20, 30, 48)
_TEXT_COLOUR = (220, 220, 220)
_BTN_COLOUR = (50, 70, 100)
_BTN_HOVER_COLOUR = (80, 110, 160)
_BTN_READY_COLOUR = (60, 140, 80)
_BTN_DISABLED_COLOUR = (40, 50, 65)
_BTN_TEXT_COLOUR = (230, 230, 230)
_BTN_TEXT_DISABLED = (100, 100, 110)

# Layout constants — board occupies the left 75 % of the window.
_BOARD_FRACTION: float = 0.75
_BOARD_COLS: int = 10
_BOARD_ROWS: int = 10

# Lake positions (must match board.py _LAKE_POSITIONS).
_LAKE_POSITIONS: frozenset[tuple[int, int]] = frozenset(
    {
        (4, 2), (4, 3), (5, 2), (5, 3),
        (4, 6), (4, 7), (5, 6), (5, 7),
    }
)

# Setup zone row ranges per side (matches board.py).
_SETUP_ZONES: dict[PlayerSide, tuple[int, int]] = {
    PlayerSide.RED: (6, 9),
    PlayerSide.BLUE: (0, 3),
}


class SetupScreen(Screen):
    """Screen that lets a player place their 40 pieces before the game begins.

    The screen maintains:
    - ``piece_tray``: the list of pieces not yet placed.
    - ``placed_pieces``: the list of pieces that have been placed on the board.
    - ``is_ready``: ``True`` when all 40 pieces have been placed.

    Keyboard shortcuts:
    - **A** — Auto-arrange all remaining pieces randomly.
    - **C** — Clear all placed pieces back to the tray.
    - **R** — Confirm ready (only effective when ``is_ready`` is ``True``).
    - **Q** — Quit / go back to the main menu.
    """

    def __init__(
        self,
        game_controller: Any,
        screen_manager: Any,
        player_side: PlayerSide,
        army: list[Rank],
        event_bus: EventBus | None = None,
        renderer: Any = None,
        viewing_player: PlayerSide = PlayerSide.RED,
    ) -> None:
        """Initialise the setup screen.

        Args:
            game_controller: The ``GameController`` for submitting ``PlacePiece``
                commands.
            screen_manager: The ``ScreenManager`` for navigation.
            player_side: Which player is setting up their army.
            army: Ordered list of ``Rank`` values to place (typically 40 items).
            event_bus: Optional ``EventBus`` — forwarded to ``PlayingScreen``
                when the player clicks Ready.  When ``None``, the Ready
                transition is suppressed (useful in unit tests).
            renderer: Optional renderer adapter — forwarded to ``PlayingScreen``.
                When ``None``, the Ready transition is suppressed.
            viewing_player: The player perspective passed to ``PlayingScreen``.
        """
        self._controller = game_controller
        self._screen_manager = screen_manager
        self._player_side = player_side
        self._army = army
        self._event_bus = event_bus
        self._renderer = renderer
        self._viewing_player = viewing_player
        self._piece_tray: list[Piece] = []
        self._placed_pieces: list[Piece] = []
        self._occupied_positions: set[tuple[int, int]] = set()
        self._font: Any = None
        self._font_small: Any = None
        self._mouse_pos: tuple[int, int] = (0, 0)

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, data: dict[str, Any]) -> None:
        """Populate the piece tray from the army list.

        Args:
            data: Context data.  May contain ``event_bus``, ``renderer``, and
                ``viewing_player`` to override the values supplied at
                construction time.
        """
        if "event_bus" in data:
            self._event_bus = data["event_bus"]
        if "renderer" in data:
            self._renderer = data["renderer"]
        if "viewing_player" in data:
            self._viewing_player = data["viewing_player"]

        self._piece_tray = [
            Piece(
                rank=rank,
                owner=self._player_side,
                revealed=False,
                has_moved=False,
                position=Position(0, 0),  # Placeholder — overridden on placement.
            )
            for rank in sorted(self._army)
        ]
        self._placed_pieces = []
        self._occupied_positions = set()

        if _pygame is None:
            return
        if not _pygame.get_init():
            _pygame.init()
        _pygame.font.init()
        self._font = _pygame.font.SysFont("Arial", 24)
        self._font_small = _pygame.font.SysFont("Arial", 18)

    def on_exit(self) -> dict[str, Any]:
        """Return the current game state to the next screen.

        Returns:
            A dict containing the controller's current ``GameState`` under
            the key ``"game_state"``.
        """
        return {"game_state": self._controller.current_state}

    def render(self, surface: Any) -> None:
        """Render the setup screen — board background and on-screen buttons.

        Args:
            surface: The target ``pygame.Surface`` (may be ``None`` in
                headless test environments).
        """
        if surface is None or _pygame is None:
            return

        w: int = surface.get_width()
        h: int = surface.get_height()
        surface.fill(_BG_COLOUR)

        # Board area: delegate to the renderer if available.
        if self._renderer is not None:
            self._renderer.render(self._controller.current_state)

        # Side panel.
        panel_x = int(w * _BOARD_FRACTION)
        panel_w = w - panel_x
        _pygame.draw.rect(surface, (30, 45, 70), (panel_x, 0, panel_w, h))

        cx = panel_x + panel_w // 2

        if self._font is not None:
            title = self._font.render("Setup Phase", True, _TEXT_COLOUR)
            surface.blit(title, title.get_rect(center=(cx, 40)))

            remaining = self._font.render(
                f"Pieces left: {len(self._piece_tray)}", True, _TEXT_COLOUR
            )
            surface.blit(remaining, remaining.get_rect(center=(cx, 80)))

        # Buttons in the panel.
        btn_w, btn_h = 160, 40
        btn_x = cx - btn_w // 2

        buttons = [
            ("Auto [A]", 140, False, self.auto_arrange),
            ("Clear [C]", 200, False, self.clear),
            ("Abandon [Q]", 260, False, self._on_abandon),
            ("Ready [R]", 320, not self.is_ready, self._on_ready),
        ]
        for label, y, disabled, _ in buttons:
            colour = _BTN_DISABLED_COLOUR if disabled else _BTN_COLOUR
            rect = _pygame.Rect(btn_x, y, btn_w, btn_h)
            _pygame.draw.rect(surface, colour, rect, border_radius=8)
            text_colour = _BTN_TEXT_DISABLED if disabled else _BTN_TEXT_COLOUR
            font = self._font_small or self._font
            if font is not None:
                lbl = font.render(label, True, text_colour)
                surface.blit(lbl, lbl.get_rect(center=rect.center))

    def handle_event(self, event: Any) -> None:
        """Handle input events.

        Keyboard shortcuts: A = auto-arrange, C = clear, R = ready (if set),
        Q = abandon setup and return to main menu.

        Mouse: left-click on the side-panel buttons triggers the same actions.

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

        if event.type == _KEYDOWN:
            key = event.key
            if key == _pygame.K_a:
                self.auto_arrange()
            elif key == _pygame.K_c:
                self.clear()
            elif key == _pygame.K_r and self.is_ready:
                self._on_ready()
            elif key == _pygame.K_q:
                self._on_abandon()
            return

        if event.type == _MOUSEBUTTONDOWN and event.button == 1:
            self._handle_mouse_click(event.pos)

    def update(self, delta_time: float) -> None:
        """Advance per-frame logic (no-op for setup screen).

        Args:
            delta_time: Elapsed time since the previous frame, in seconds.
        """

    # ------------------------------------------------------------------
    # Tray / placement API (used by tests and the UI layer)
    # ------------------------------------------------------------------

    @property
    def piece_tray(self) -> list[Piece]:
        """Pieces not yet placed on the board, in rank order."""
        return self._piece_tray

    @property
    def placed_pieces(self) -> list[Piece]:
        """Pieces that have been successfully placed on the board."""
        return self._placed_pieces

    @property
    def is_ready(self) -> bool:
        """``True`` iff all pieces have been placed (tray is empty)."""
        return len(self._piece_tray) == 0

    def _is_valid_position(self, pos: Position) -> bool:
        """Return ``True`` iff *pos* is a valid placement position.

        Checks:
        - Not a lake square.
        - Within this player's setup zone.
        - Not already occupied by a previously placed piece.
        """
        key = (pos.row, pos.col)
        if key in _LAKE_POSITIONS:
            return False
        low, high = _SETUP_ZONES[self._player_side]
        if not (low <= pos.row <= high):
            return False
        if key in self._occupied_positions:
            return False
        return True

    def place_piece(self, piece: Piece, pos: Position) -> bool:
        """Attempt to place *piece* at *pos*.

        If the placement is valid (within the player's setup zone, not a lake,
        not already occupied) the piece is removed from the tray, a
        ``PlacePiece`` command is submitted to the controller, and the placed
        piece is added to ``placed_pieces``.

        Args:
            piece: The piece to place (must be in ``piece_tray``).
            pos: The target board position.

        Returns:
            ``True`` if the placement succeeded, ``False`` otherwise.
        """
        if not self._is_valid_position(pos):
            return False

        # Remove piece from tray.
        try:
            self._piece_tray.remove(piece)
        except ValueError:
            return False

        # Submit command to controller.
        self._controller.submit_command(PlacePiece(piece=piece, pos=pos))

        # Track placed piece.
        placed = Piece(
            rank=piece.rank,
            owner=piece.owner,
            revealed=False,
            has_moved=False,
            position=pos,
        )
        self._placed_pieces.append(placed)
        self._occupied_positions.add((pos.row, pos.col))
        return True

    def auto_arrange(self) -> None:
        """Randomly place all remaining tray pieces in the player's setup zone.

        Pieces are placed one by one in random valid positions.  This method
        submits one ``PlacePiece`` command per piece.
        """
        low, high = _SETUP_ZONES[self._player_side]
        all_positions = [
            Position(row, col)
            for row in range(low, high + 1)
            for col in range(10)
        ]
        random.shuffle(all_positions)

        pos_index = 0
        tray_snapshot = list(self._piece_tray)
        for piece in tray_snapshot:
            while pos_index < len(all_positions):
                pos = all_positions[pos_index]
                pos_index += 1
                if self.place_piece(piece, pos):
                    break

    def clear(self) -> None:
        """Remove all placed pieces and return them to the piece tray.

        The game controller state is *not* reset here (that must be done at a
        higher level); this method only manages the tray bookkeeping for UI
        purposes.
        """
        returned = [
            Piece(
                rank=p.rank,
                owner=p.owner,
                revealed=False,
                has_moved=False,
                position=Position(0, 0),
            )
            for p in self._placed_pieces
        ]
        self._piece_tray = sorted(
            list(self._piece_tray) + returned, key=lambda p: p.rank
        )
        self._placed_pieces = []
        self._occupied_positions = set()

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def _on_ready(self) -> None:
        """Transition to ``PlayingScreen`` when all pieces are placed.

        Requires ``event_bus`` and ``renderer`` to have been supplied at
        construction time or via ``on_enter(data)``.  If either is ``None``
        this method is a no-op (e.g. in unit-test contexts).
        """
        if not self.is_ready:
            return
        if self._event_bus is None or self._renderer is None:
            return

        state = self._controller.current_state
        opponent_side = (
            PlayerSide.BLUE if self._player_side == PlayerSide.RED else PlayerSide.RED
        )

        # vs-AI: generate the AI setup instantly when the human is ready.
        if self._is_ai_side(opponent_side) and self._player_piece_count(opponent_side) == 0:
            self._auto_arrange_side(opponent_side)

        # Two-player: hand off to the opponent's setup screen if they have not
        # completed setup yet.
        if (
            self._is_human_side(opponent_side)
            and self._player_piece_count(opponent_side) < len(self._army)
        ):
            next_setup = SetupScreen(
                game_controller=self._controller,
                screen_manager=self._screen_manager,
                player_side=opponent_side,
                army=list(self._army),
                event_bus=self._event_bus,
                renderer=self._renderer,
                viewing_player=opponent_side,
            )
            self._screen_manager.replace(next_setup)
            return

        # Both sides are now set up — switch to PLAYING phase before entering
        # the playing screen.
        state = self._controller.current_state
        self._controller._state = dc_replace(  # noqa: SLF001
            state,
            phase=GamePhase.PLAYING,
            active_player=PlayerSide.RED,
        )

        from src.presentation.screens.playing_screen import PlayingScreen

        playing_screen = PlayingScreen(
            controller=self._controller,
            screen_manager=self._screen_manager,
            event_bus=self._event_bus,
            renderer=self._renderer,
            viewing_player=self._viewing_player,
        )
        self._screen_manager.replace(playing_screen)

    def _on_abandon(self) -> None:
        """Pop back to the previous screen (main menu or start-game screen)."""
        try:
            self._screen_manager.pop()
        except IndexError:
            pass

    def _handle_mouse_click(self, pixel_pos: tuple[int, int]) -> None:
        """Handle a left mouse-button click in the setup screen.

        Clicks in the side panel activate the Auto-arrange, Clear, and Ready
        buttons.

        Args:
            pixel_pos: The (x, y) pixel coordinates of the click.
        """
        if _pygame is None:
            return
        try:
            surface = _pygame.display.get_surface()
            if surface is not None:
                w = surface.get_width()
                h = surface.get_height()
            else:
                info = _pygame.display.Info()
                w = info.current_w or 1024
                h = info.current_h or 768
        except Exception:
            return

        board_w = int(w * _BOARD_FRACTION)
        cell_w = board_w // _BOARD_COLS
        cell_h = h // _BOARD_ROWS

        # Board click: place the next tray piece on the clicked setup square.
        px, py = pixel_pos
        if px < board_w and cell_w > 0 and cell_h > 0:
            col = min(px // cell_w, _BOARD_COLS - 1)
            row = min(py // cell_h, _BOARD_ROWS - 1)
            if self._piece_tray:
                self.place_piece(self._piece_tray[0], Position(row, col))
            return

        panel_x = int(w * _BOARD_FRACTION)
        panel_w = w - panel_x
        cx = panel_x + panel_w // 2
        btn_w, btn_h = 160, 40
        btn_x = cx - btn_w // 2

        button_rects = [
            (btn_x, 140, btn_w, btn_h, self.auto_arrange),
            (btn_x, 200, btn_w, btn_h, self.clear),
            (btn_x, 260, btn_w, btn_h, self._on_abandon),
            (btn_x, 320, btn_w, btn_h, self._on_ready),
        ]
        for bx, by, bw, bh, action in button_rects:
            rect = _pygame.Rect(bx, by, bw, bh)
            if rect.collidepoint(pixel_pos):
                action()
                return

    def _player_piece_count(self, side: PlayerSide) -> int:
        """Return the number of placed pieces for *side* in current state."""
        state = self._controller.current_state
        for player in state.players:
            if player.side == side:
                return len(player.pieces_remaining)
        return 0

    def _is_ai_side(self, side: PlayerSide) -> bool:
        """Return True iff *side* is controlled by an AI player."""
        state = self._controller.current_state
        for player in state.players:
            if player.side == side:
                return player.player_type in {
                    PlayerType.AI_EASY,
                    PlayerType.AI_MEDIUM,
                    PlayerType.AI_HARD,
                }
        return False

    def _is_human_side(self, side: PlayerSide) -> bool:
        """Return True iff *side* is a human player."""
        state = self._controller.current_state
        for player in state.players:
            if player.side == side:
                return bool(player.player_type == PlayerType.HUMAN)
        return False

    def _auto_arrange_side(self, side: PlayerSide) -> None:
        """Auto-place a full army for *side* using random valid setup squares."""
        low, high = _SETUP_ZONES[side]
        positions = [
            Position(row, col)
            for row in range(low, high + 1)
            for col in range(_BOARD_COLS)
        ]
        random.shuffle(positions)

        pos_index = 0
        for rank in sorted(self._army):
            while pos_index < len(positions):
                pos = positions[pos_index]
                pos_index += 1
                piece = Piece(
                    rank=rank,
                    owner=side,
                    revealed=False,
                    has_moved=False,
                    position=Position(0, 0),
                )
                self._controller.submit_command(PlacePiece(piece=piece, pos=pos))
                break
