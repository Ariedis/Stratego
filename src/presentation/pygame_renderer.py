"""
src/presentation/pygame_renderer.py

PygameRenderer — draws the Stratego board and pieces onto a pygame Surface.
Specification: system_design.md §2.4; game_components.md §3.2
"""
from __future__ import annotations

from typing import Any

from src.domain.enums import PlayerSide, TerrainType
from src.domain.game_state import GameState
from src.domain.piece import Position
from src.presentation.sprite_manager import SpriteManager

# Layout constants — board occupies the left 75 % of the window.
_BOARD_FRACTION: float = 0.75
_BOARD_ROWS: int = 10
_BOARD_COLS: int = 10


class PygameRenderer:
    """Renders the Stratego board onto a ``pygame.Surface`` with fog-of-war.

    The board is drawn in the left ``_BOARD_FRACTION`` portion of the window.
    Each of the 100 squares is drawn with a tile, and pieces are blitted on
    top.  Opponent unrevealed pieces use the hidden surface from
    ``SpriteManager``.
    """

    def __init__(self, screen: Any, sprite_manager: SpriteManager) -> None:
        """Initialise the renderer.

        Args:
            screen: The pygame display surface (or mock in tests).
            sprite_manager: Provides piece and tile surfaces.
        """
        self._screen = screen
        self._sprite_manager = sprite_manager

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def render(self, state: GameState, viewing_player: PlayerSide) -> None:
        """Draw the full board onto the screen surface.

        Applies fog-of-war: opponent pieces that have not been revealed are
        drawn with the hidden surface.

        Args:
            state: The current ``GameState`` to render.
            viewing_player: The player whose perspective determines which
                opponent pieces are hidden.
        """
        window_width: int = self._screen.get_width()
        window_height: int = self._screen.get_height()
        board_width = int(window_width * _BOARD_FRACTION)
        cell_w = board_width // _BOARD_COLS
        cell_h = window_height // _BOARD_ROWS

        # Fill background.
        self._screen.fill((30, 30, 30))

        board = state.board

        for row in range(_BOARD_ROWS):
            for col in range(_BOARD_COLS):
                x = col * cell_w
                y = row * cell_h
                sq = board.get_square(Position(row, col))

                # Choose tile surface.
                if sq.terrain == TerrainType.LAKE:
                    tile = self._sprite_manager.lake_surface
                else:
                    tile = self._sprite_manager.empty_surface

                self._screen.blit(tile, (x, y))

                # Draw piece (if any) on top of tile.
                if sq.piece is not None:
                    piece = sq.piece
                    # Fog-of-war: hide opponent unrevealed pieces.
                    is_own = piece.owner == viewing_player
                    show_revealed = is_own or piece.revealed
                    surface = self._sprite_manager.get_surface(
                        rank=piece.rank,
                        owner=piece.owner,
                        revealed=show_revealed,
                    )
                    self._screen.blit(surface, (x, y))
