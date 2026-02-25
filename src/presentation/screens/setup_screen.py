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
_BTN_HOVER_COLOUR = (72, 100, 144)  # COLOUR_BTN_HOVER
_BTN_READY_COLOUR = (41, 128, 185)  # COLOUR_BTN_PRIMARY
_BTN_DANGER_COLOUR = (192, 57, 43)  # COLOUR_BTN_DANGER (for Abandon)
_BTN_DISABLED_COLOUR = (40, 50, 65)
_BTN_TEXT_COLOUR = (230, 230, 230)
_BTN_TEXT_DISABLED = (100, 110, 125)
_SETUP_ZONE_BORDER_COLOUR = (220, 180, 80)  # COLOUR_TITLE_GOLD — setup zone guide
_TEAM_RED_COLOUR = (200, 60, 60)    # COLOUR_TEAM_RED
_TEAM_BLUE_COLOUR = (60, 110, 210)  # COLOUR_TEAM_BLUE
_COLOUR_SELECT = (80, 160, 80)      # COLOUR_SELECT — highlighted tray row
_COLOUR_INVALID = (200, 60, 60)     # invalid placement flash
_COLOUR_TRAY_ROW = (35, 52, 80)     # default tray row background
_COLOUR_SURFACE = (40, 58, 88)      # handover overlay card background
_COLOUR_DEPLETED = (120, 40, 40)    # count badge when rank exhausted

# Piece tray display order (Marshal → Flag, matching the wireframe)
_TRAY_ORDER: list[Rank] = [
    Rank.MARSHAL, Rank.GENERAL, Rank.COLONEL, Rank.MAJOR,
    Rank.CAPTAIN, Rank.LIEUTENANT, Rank.SERGEANT, Rank.MINER,
    Rank.SCOUT, Rank.SPY, Rank.BOMB, Rank.FLAG,
]

_RANK_NAMES: dict[Rank, str] = {
    Rank.MARSHAL: "Marshal",
    Rank.GENERAL: "General",
    Rank.COLONEL: "Colonel",
    Rank.MAJOR: "Major",
    Rank.CAPTAIN: "Captain",
    Rank.LIEUTENANT: "Lieutenant",
    Rank.SERGEANT: "Sergeant",
    Rank.MINER: "Miner",
    Rank.SCOUT: "Scout",
    Rank.SPY: "Spy",
    Rank.BOMB: "Bomb",
    Rank.FLAG: "Flag",
}

# Duration (seconds) of the invalid-cell flash highlight.
_FLASH_DURATION: float = 0.5
# Height (px) of each tray row in the side panel.
_TRAY_ROW_H: int = 20

# Layout constants — board occupies the left 80 % of the window.
_BOARD_FRACTION: float = 0.80
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
        # Tray selection: which rank is the "next to place".
        self._selected_rank: Rank | None = None
        # Cells currently flashing COLOUR_INVALID (row, col) → remaining seconds.
        self._invalid_flash_cells: dict[tuple[int, int], float] = {}
        # Remaining duration of the "Place pieces in your setup zone" error label.
        self._error_label_timer: float = 0.0
        # Handover overlay shown between player 1 ready and player 2 setup.
        self._show_handover_overlay: bool = False
        self._pending_handover_screen: SetupScreen | None = None

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
        self._selected_rank = None
        self._invalid_flash_cells = {}
        self._error_label_timer = 0.0
        self._show_handover_overlay = False
        self._pending_handover_screen = None

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

        # Setup zone highlight (gold border around the player's setup rows).
        board_w = int(w * _BOARD_FRACTION)
        if board_w > 0 and h > 0:
            cell_h = h // _BOARD_ROWS
            low, high = _SETUP_ZONES[self._player_side]
            zone_y = low * cell_h
            zone_h = (high - low + 1) * cell_h
            _pygame.draw.rect(
                surface,
                _SETUP_ZONE_BORDER_COLOUR,
                _pygame.Rect(0, zone_y, board_w, zone_h),
                3,
            )

        # Invalid-cell flash overlays drawn on top of the board.
        if self._invalid_flash_cells and board_w > 0 and h > 0:
            cell_w_board = board_w // _BOARD_COLS
            cell_h_board = h // _BOARD_ROWS
            flash_surf = _pygame.Surface((cell_w_board, cell_h_board), _pygame.SRCALPHA)
            flash_surf.fill((*_COLOUR_INVALID, 160))
            for (r, c) in list(self._invalid_flash_cells):
                surface.blit(flash_surf, (c * cell_w_board, r * cell_h_board))

        # Error label for out-of-zone clicks.
        if self._error_label_timer > 0 and self._font_small is not None:
            err_lbl = self._font_small.render(
                "Place pieces in your setup zone", True, _COLOUR_INVALID
            )
            surface.blit(err_lbl, err_lbl.get_rect(centerx=board_w // 2, top=4))

        # Side panel.
        panel_x = int(w * _BOARD_FRACTION)
        panel_w = w - panel_x
        _pygame.draw.rect(surface, (30, 45, 70), (panel_x, 0, panel_w, h))

        cx = panel_x + panel_w // 2

        if self._font is not None:
            title = self._font.render("Setup", True, _TEXT_COLOUR)
            surface.blit(title, title.get_rect(center=(cx, 28)))

            # Player identity label (wireframe annotation 5)
            player_num = "1" if self._player_side == PlayerSide.RED else "2"
            army_name = "Red Army" if self._player_side == PlayerSide.RED else "Blue Army"
            player_label_text = f"Player {player_num} \u2014 {army_name}"
            player_colour = (
                _TEAM_RED_COLOUR if self._player_side == PlayerSide.RED else _TEAM_BLUE_COLOUR
            )
            player_label = self._font.render(player_label_text, True, player_colour)
            surface.blit(player_label, player_label.get_rect(center=(cx, 58)))

        # Rank-grouped piece tray (wireframe annotation 3).
        if self._font_small is not None:
            tray_header = self._font_small.render("Remaining Pieces", True, _TEXT_COLOUR)
            surface.blit(tray_header, tray_header.get_rect(center=(cx, 88)))

            tray_rects = self._get_tray_row_rects(panel_x, panel_w)
            from collections import Counter
            counts: Counter[Rank] = Counter(p.rank for p in self._piece_tray)
            for rank, rect in zip(_TRAY_ORDER, tray_rects):
                count = counts.get(rank, 0)
                is_selected = rank == self._selected_rank
                is_depleted = count == 0
                bg_colour = _COLOUR_SELECT if is_selected else _COLOUR_TRAY_ROW
                _pygame.draw.rect(surface, bg_colour, rect, border_radius=4)

                rank_text = _RANK_NAMES.get(rank, rank.name.title())
                txt_colour = _BTN_TEXT_DISABLED if is_depleted else _TEXT_COLOUR
                name_surf = self._font_small.render(rank_text, True, txt_colour)
                surface.blit(name_surf, name_surf.get_rect(midleft=(rect.x + 6, rect.centery)))

                count_colour = _COLOUR_DEPLETED if is_depleted else _TEXT_COLOUR
                count_surf = self._font_small.render(f"({count})", True, count_colour)
                surface.blit(
                    count_surf, count_surf.get_rect(midright=(rect.right - 6, rect.centery))
                )

        # Buttons in the panel — anchored near the bottom.
        btn_w, btn_h = 160, 40
        btn_x = cx - btn_w // 2
        btn_y_auto = h - 220
        # (label, y, disabled, colour)
        btn_specs = [
            ("Auto [A]",    btn_y_auto,       False,             _BTN_COLOUR),
            ("Clear [C]",   btn_y_auto + 50,  False,             _BTN_COLOUR),
            ("Abandon [Q]", btn_y_auto + 100, False,             _BTN_DANGER_COLOUR),
            ("Ready [R]",   btn_y_auto + 160, not self.is_ready, _BTN_READY_COLOUR),
        ]
        for label, y, disabled, btn_colour in btn_specs:
            colour = _BTN_DISABLED_COLOUR if disabled else btn_colour
            rect = _pygame.Rect(btn_x, y, btn_w, btn_h)
            _pygame.draw.rect(surface, colour, rect, border_radius=8)
            text_colour = _BTN_TEXT_DISABLED if disabled else _BTN_TEXT_COLOUR
            font = self._font_small or self._font
            if font is not None:
                lbl = font.render(label, True, text_colour)
                surface.blit(lbl, lbl.get_rect(center=rect.center))

        # Handover overlay — full-screen opaque scrim + centred card.
        if self._show_handover_overlay:
            scrim = _pygame.Surface((w, h))
            scrim.fill((0, 0, 0))
            scrim.set_alpha(230)
            surface.blit(scrim, (0, 0))

            card_w, card_h = min(680, w - 80), 220
            card_x = (w - card_w) // 2
            card_y = (h - card_h) // 2
            _pygame.draw.rect(
                surface, _COLOUR_SURFACE,
                _pygame.Rect(card_x, card_y, card_w, card_h),
                border_radius=12,
            )

            font_heading = self._font or self._font_small
            font_body = self._font_small or self._font
            if font_heading is not None:
                line1 = font_heading.render(
                    "Player 1 has finished army setup.", True, _TEXT_COLOUR
                )
                surface.blit(line1, line1.get_rect(center=(w // 2, card_y + 60)))
            if font_body is not None:
                line2 = font_body.render(
                    "Please pass the device to Player 2.", True, _TEXT_COLOUR
                )
                surface.blit(line2, line2.get_rect(center=(w // 2, card_y + 110)))
                line3 = font_body.render(
                    "Player 2: press any key or click to continue.", True, _TEXT_COLOUR
                )
                surface.blit(line3, line3.get_rect(center=(w // 2, card_y + 155)))

    def handle_event(self, event: Any) -> None:
        """Handle input events.

        Keyboard shortcuts: A = auto-arrange, C = clear, R = ready (if set),
        Q = abandon setup and return to main menu.  Tab / ↑ / ↓ navigate the
        tray.

        Mouse: left-click on the side-panel buttons triggers the same actions.
        Clicking a tray row selects that piece type as "next to place".
        Clicking a board cell places the selected piece type.

        When the handover overlay is visible, any key press or mouse click
        dismisses it and proceeds to Player 2's setup screen.

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

        # Handover overlay: consume all events until dismissed.
        if self._show_handover_overlay:
            if event.type in (_KEYDOWN, _MOUSEBUTTONDOWN):
                self._dismiss_handover_overlay()
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
            elif key in (_pygame.K_TAB, _pygame.K_DOWN):
                self._cycle_tray_selection(1)
            elif key == _pygame.K_UP:
                self._cycle_tray_selection(-1)
            return

        if event.type == _MOUSEBUTTONDOWN and event.button == 1:
            self._handle_mouse_click(event.pos)

    def update(self, delta_time: float) -> None:
        """Advance per-frame logic — tick down invalid-cell flash timers.

        Args:
            delta_time: Elapsed time since the previous frame, in seconds.
        """
        expired = [k for k, t in self._invalid_flash_cells.items() if t <= 0]
        for k in expired:
            del self._invalid_flash_cells[k]
        for k in list(self._invalid_flash_cells):
            self._invalid_flash_cells[k] -= delta_time
        if self._error_label_timer > 0:
            self._error_label_timer -= delta_time

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
        """Transition to the next phase when all pieces are placed.

        In 2-player mode, shows the full-screen handover overlay so Player 1's
        arrangement is hidden while the device is passed to Player 2.  The
        actual screen transition happens when the overlay is dismissed
        (any key or click).

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

        # Two-player: show handover overlay, then go to the opponent's setup.
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
            self._pending_handover_screen = next_setup
            self._show_handover_overlay = True
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

        - Board area: places the selected/next tray piece on the clicked cell;
          flashes the cell ``COLOUR_INVALID`` if the click is outside the
          player's setup zone (annotation 4).
        - Tray rows: selects that rank as "next to place".
        - Side-panel buttons: trigger Auto-arrange, Clear, Abandon, or Ready.

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

        # Board click: attempt to place the selected/next tray piece.
        px, py = pixel_pos
        if px < board_w and cell_w > 0 and cell_h > 0:
            col = min(px // cell_w, _BOARD_COLS - 1)
            row = min(py // cell_h, _BOARD_ROWS - 1)
            if self._piece_tray:
                piece = self._find_tray_piece()
                if piece is not None:
                    placed = self.place_piece(piece, Position(row, col))
                    if not placed:
                        # Flash the invalid cell (annotation 4).
                        self._invalid_flash_cells[(row, col)] = _FLASH_DURATION
                        self._error_label_timer = _FLASH_DURATION
            return

        panel_x = int(w * _BOARD_FRACTION)
        panel_w = w - panel_x
        cx = panel_x + panel_w // 2
        btn_w_size, btn_h_size = 160, 40
        btn_x = cx - btn_w_size // 2

        # Tray row clicks: select a rank.
        tray_rects = self._get_tray_row_rects(panel_x, panel_w)
        for rank, rect in zip(_TRAY_ORDER, tray_rects):
            if rect.collidepoint(pixel_pos):
                # Toggle off if already selected; otherwise select the new rank.
                from collections import Counter
                counts: Counter[Rank] = Counter(p.rank for p in self._piece_tray)
                if counts.get(rank, 0) > 0:
                    self._selected_rank = rank
                return

        btn_y_auto = h - 220
        button_rects = [
            (btn_x, btn_y_auto,       btn_w_size, btn_h_size, self.auto_arrange),
            (btn_x, btn_y_auto + 50,  btn_w_size, btn_h_size, self.clear),
            (btn_x, btn_y_auto + 100, btn_w_size, btn_h_size, self._on_abandon),
            (btn_x, btn_y_auto + 160, btn_w_size, btn_h_size, self._on_ready),
        ]
        for bx, by, bw, bh, action in button_rects:
            rect = _pygame.Rect(bx, by, bw, bh)
            if rect.collidepoint(pixel_pos):
                action()
                return

    def _dismiss_handover_overlay(self) -> None:
        """Hide the handover overlay and perform the pending screen transition."""
        self._show_handover_overlay = False
        pending = self._pending_handover_screen
        self._pending_handover_screen = None
        if pending is not None:
            self._screen_manager.replace(pending)

    def _find_tray_piece(self) -> Piece | None:
        """Return the next piece to place, respecting the current tray selection.

        Returns the first piece in the tray whose rank matches
        ``_selected_rank``, or the first piece overall if no rank is selected
        or the selected rank is exhausted.

        Returns:
            A ``Piece`` from the tray, or ``None`` if the tray is empty.
        """
        if not self._piece_tray:
            return None
        if self._selected_rank is not None:
            for p in self._piece_tray:
                if p.rank == self._selected_rank:
                    return p
        return self._piece_tray[0]

    def _cycle_tray_selection(self, direction: int) -> None:
        """Advance the tray selection forward or backward among available ranks.

        Only ranks that still have at least one piece in the tray are cycled
        through.

        Args:
            direction: ``+1`` to advance forwards (Tab / ↓), ``-1`` for ↑.
        """
        available = [r for r in _TRAY_ORDER if any(p.rank == r for p in self._piece_tray)]
        if not available:
            return
        if self._selected_rank not in available:
            self._selected_rank = available[0]
            return
        idx = available.index(self._selected_rank)
        self._selected_rank = available[(idx + direction) % len(available)]

    def _get_tray_row_rects(self, panel_x: int, panel_w: int) -> list[Any]:
        """Return a list of pygame.Rect objects for each tray row.

        Rows are ordered to match ``_TRAY_ORDER``.  The rects are used for
        both rendering and mouse-hit detection.

        Args:
            panel_x: Left edge of the side panel in screen pixels.
            panel_w: Width of the side panel in pixels.

        Returns:
            A list of 12 ``pygame.Rect`` objects.
        """
        if _pygame is None:
            return []
        margin = 6
        row_w = panel_w - margin * 2
        tray_y_start = 102
        rects = []
        for i in range(len(_TRAY_ORDER)):
            rects.append(
                _pygame.Rect(
                    panel_x + margin,
                    tray_y_start + i * _TRAY_ROW_H,
                    row_w,
                    _TRAY_ROW_H - 2,
                )
            )
        return rects

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
