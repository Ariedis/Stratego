"""
src/presentation/terminal_renderer.py

ASCII terminal renderer for the Stratego board.
Specification: system_design.md §2.4; game_components.md §3.2
"""
from __future__ import annotations

from src.domain.enums import PlayerSide, Rank, TerrainType
from src.domain.game_state import GameState
from src.domain.piece import Piece, Position

# Width of each cell in characters (4 characters: e.g. " M10", " SPY", " ~~ ")
_CELL_WIDTH = 4

# Abbreviations for each rank (3 chars max, left-padded with space to 4 total)
_RANK_ABBR: dict[Rank, str] = {
    Rank.FLAG: "FLG",
    Rank.SPY: "SPY",
    Rank.SCOUT: "SCO",
    Rank.MINER: "MIN",
    Rank.SERGEANT: "SGT",
    Rank.LIEUTENANT: "LT ",
    Rank.CAPTAIN: "CAP",
    Rank.MAJOR: "MAJ",
    Rank.COLONEL: "COL",
    Rank.GENERAL: "GEN",
    Rank.MARSHAL: "MAR",
    Rank.BOMB: "BMB",
}


def _cell_str(piece: Piece | None, terrain: TerrainType, viewing_player: PlayerSide) -> str:
    """Return a 4-character string for a single board cell."""
    if terrain == TerrainType.LAKE:
        return " ~~ "
    if piece is None:
        return " .. "
    # Own piece: always show rank.
    if piece.owner == viewing_player:
        return f" {_RANK_ABBR[piece.rank]}"
    # Opponent unrevealed: fog-of-war.
    if not piece.revealed:
        return "[?] "
    # Opponent revealed: show rank with bracket.
    abbr = _RANK_ABBR[piece.rank]
    return f"[{abbr[:2]}]"


class TerminalRenderer:
    """Renders a ``GameState`` as an ASCII grid to ``stdout``.

    The board is printed as a 10-row × 10-column grid.  Fog-of-war is
    applied: the opponent's unrevealed pieces are shown as ``[?]``.
    """

    def render(self, state: GameState, viewing_player: PlayerSide) -> None:
        """Print the board to stdout from *viewing_player*'s perspective.

        Args:
            state: The current ``GameState`` to render.
            viewing_player: The player whose perspective determines which
                opponent pieces are hidden.
        """
        board = state.board
        for row in range(10):
            cells: list[str] = []
            for col in range(10):
                sq = board.get_square(Position(row, col))
                cells.append(_cell_str(sq.piece, sq.terrain, viewing_player))
            print("".join(cells))
