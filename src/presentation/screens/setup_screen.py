"""
src/presentation/screens/setup_screen.py

SetupScreen — piece placement UI for the Stratego setup phase.
Specification: screen_flow.md §3.6; system_design.md §2.4
"""
from __future__ import annotations

import random
from typing import Any

from src.application.commands import PlacePiece
from src.domain.enums import PlayerSide, Rank
from src.domain.piece import Piece, Position
from src.presentation.screens.base import Screen

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
    """

    def __init__(
        self,
        game_controller: Any,
        screen_manager: Any,
        player_side: PlayerSide,
        army: list[Rank],
    ) -> None:
        """Initialise the setup screen.

        Args:
            game_controller: The ``GameController`` for submitting ``PlacePiece``
                commands.
            screen_manager: The ``ScreenManager`` for navigation.
            player_side: Which player is setting up their army.
            army: Ordered list of ``Rank`` values to place (typically 40 items).
        """
        self._controller = game_controller
        self._screen_manager = screen_manager
        self._player_side = player_side
        self._army = army
        self._piece_tray: list[Piece] = []
        self._placed_pieces: list[Piece] = []
        self._occupied_positions: set[tuple[int, int]] = set()

    # ------------------------------------------------------------------
    # Screen lifecycle
    # ------------------------------------------------------------------

    def on_enter(self, data: dict[str, Any]) -> None:
        """Populate the piece tray from the army list.

        Args:
            data: Context data (ignored for initial setup).
        """
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

    def on_exit(self) -> dict[str, Any]:
        """Return the current game state to the next screen.

        Returns:
            A dict containing the controller's current ``GameState`` under
            the key ``"game_state"``.
        """
        return {"game_state": self._controller.current_state}

    def render(self, surface: Any) -> None:
        """Render the setup screen (stub — visual rendering is platform-specific)."""

    def handle_event(self, event: Any) -> None:
        """Handle input events (stub — full drag-and-drop wired in subclass)."""

    def update(self, delta_time: float) -> None:
        """Advance per-frame logic (stub)."""

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
