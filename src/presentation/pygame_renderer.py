"""
src/presentation/pygame_renderer.py

PygameRenderer — draws the Stratego board and pieces onto a pygame Surface.
Specification: system_design.md §2.4; game_components.md §3.2
"""
from __future__ import annotations

from typing import Any

from src.domain.enums import PlayerSide, Rank, TerrainType
from src.domain.game_state import GameState
from src.domain.piece import Position
from src.presentation.sprite_manager import SpriteManager

# Layout constants — board occupies the left 80 % of the window (wireframe §1).
_BOARD_FRACTION: float = 0.80
_BOARD_ROWS: int = 10
_BOARD_COLS: int = 10

# Rank abbreviations rendered inside each friendly piece cell (wireframe §4).
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

# Text colour for rank abbreviations drawn on piece tiles.
_ABBREV_COLOUR = (255, 255, 255)
_ABBREV_COLOUR_DARK = (20, 20, 20)


class PygameRenderer:
    """Renders the Stratego board onto a ``pygame.Surface`` with fog-of-war.

    The board is drawn in the left ``_BOARD_FRACTION`` portion of the window.
    Each of the 100 squares is drawn with a tile, and pieces are blitted on
    top.  Opponent unrevealed pieces use the hidden surface from
    ``SpriteManager``.  Friendly piece cells have their rank abbreviation
    drawn centred in the cell (wireframe §4).
    """

    def __init__(self, screen: Any, sprite_manager: SpriteManager) -> None:
        """Initialise the renderer.

        Args:
            screen: The pygame display surface (or mock in tests).
            sprite_manager: Provides piece and tile surfaces.
        """
        self._screen = screen
        self._sprite_manager = sprite_manager
        self._font: Any = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def render(self, state: GameState, viewing_player: PlayerSide) -> None:
        """Draw the full board onto the screen surface.

        Applies fog-of-war: opponent pieces that have not been revealed are
        drawn with the hidden surface.  Rank abbreviations are drawn centred
        on every visible (friendly or revealed) piece cell.

        Args:
            state: The current ``GameState`` to render.
            viewing_player: The player whose perspective determines which
                opponent pieces are hidden.
        """
        try:
            import pygame as _pg  # noqa: PLC0415
        except ImportError:
            _pg = None  # type: ignore[assignment]

        # Prefer the live display surface so that fullscreen toggling is seamless.
        screen: Any = self._screen
        if _pg is not None:
            live = _pg.display.get_surface()
            if live is not None:
                screen = live

        window_width: int = screen.get_width()
        window_height: int = screen.get_height()
        board_width = int(window_width * _BOARD_FRACTION)
        cell_w = board_width // _BOARD_COLS
        cell_h = window_height // _BOARD_ROWS

        # Initialise (or refresh) font when cell dimensions change.
        if _pg is not None:
            _pg.font.init()
            font_size = max(12, min(cell_w, cell_h) // 4)
            if self._font is None or getattr(self, "_last_font_size", None) != font_size:
                self._font = _pg.font.SysFont("Arial", font_size, bold=True)
                self._last_font_size: int = font_size

        # Fill background.
        screen.fill((30, 30, 30))

        board = state.board

        for row in range(_BOARD_ROWS):
            for col in range(_BOARD_COLS):
                x = col * cell_w
                y = row * cell_h
                sq = board.get_square(Position(row, col))

                # Choose tile surface and scale it to match the cell dimensions.
                if sq.terrain == TerrainType.LAKE:
                    tile = self._sprite_manager.lake_surface
                else:
                    tile = self._sprite_manager.empty_surface

                screen.blit(self._safe_scale(tile, cell_w, cell_h), (x, y))

                # Draw piece (if any) on top of tile.
                if sq.piece is not None:
                    piece = sq.piece
                    # Fog-of-war: hide opponent unrevealed pieces.
                    is_own = piece.owner == viewing_player
                    show_revealed = is_own or piece.revealed
                    piece_surface = self._sprite_manager.get_surface(
                        rank=piece.rank,
                        owner=piece.owner,
                        revealed=show_revealed,
                    )
                    screen.blit(self._safe_scale(piece_surface, cell_w, cell_h), (x, y))

                    # Draw rank abbreviation centred on visible (own or revealed) pieces.
                    if show_revealed and _pg is not None and self._font is not None:
                        abbrev = _RANK_ABBREV.get(piece.rank, "?")
                        text_colour = (
                            _ABBREV_COLOUR_DARK
                            if piece.owner == PlayerSide.RED
                            else _ABBREV_COLOUR
                        )
                        text_surf = self._font.render(abbrev, True, text_colour)
                        text_rect = text_surf.get_rect(
                            center=(x + cell_w // 2, y + cell_h // 2)
                        )
                        screen.blit(text_surf, text_rect)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _safe_scale(self, surface: Any, width: int, height: int) -> Any:
        """Return *surface* scaled to (*width*, *height*).

        Falls back to the original surface if pygame is unavailable or if
        *surface* is not a real ``pygame.Surface`` (e.g. a mock in tests).

        Args:
            surface: The source surface to scale.
            width: Target width in pixels.
            height: Target height in pixels.

        Returns:
            A scaled surface, or the original *surface* on failure.
        """
        try:
            import pygame as _pg  # noqa: PLC0415

            return _pg.transform.scale(surface, (width, height))
        except Exception:  # noqa: BLE001
            return surface
