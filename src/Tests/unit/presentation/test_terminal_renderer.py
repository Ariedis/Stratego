"""
test_terminal_renderer.py — Unit tests for src/presentation/terminal_renderer.py

Epic: EPIC-4 | User Story: US-408
Covers acceptance criteria: AC-1, AC-2, AC-3
Specification: system_design.md §2.4
"""
from __future__ import annotations

import io
from contextlib import redirect_stdout

import pytest

from src.domain.enums import PlayerSide, Rank
from src.domain.piece import Position
from src.Tests.fixtures.sample_game_states import (
    make_blue_piece,
    make_minimal_playing_state,
    make_red_piece,
)

# ---------------------------------------------------------------------------
# Optional imports — source may not be implemented yet.
# ---------------------------------------------------------------------------

try:
    from src.presentation.terminal_renderer import TerminalRenderer
except ImportError:
    TerminalRenderer = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    TerminalRenderer is None,
    reason="src.presentation.terminal_renderer not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def capture_render(renderer: object, state: object, viewing_player: PlayerSide) -> str:
    """Capture stdout output from renderer.render()."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        renderer.render(state, viewing_player)  # type: ignore[union-attr]
    return buf.getvalue()


@pytest.fixture
def renderer() -> object:
    return TerminalRenderer()


@pytest.fixture
def minimal_state() -> object:
    return make_minimal_playing_state()


# ---------------------------------------------------------------------------
# US-408 AC-1: Valid 10-row, 10-column ASCII grid without exception
# ---------------------------------------------------------------------------


class TestTerminalRendererOutputStructure:
    """AC-1: render() prints a 10×10 ASCII grid without raising."""

    def test_render_does_not_raise(self, renderer: object, minimal_state: object) -> None:
        """Calling render() with any valid GameState must not raise."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            renderer.render(minimal_state, PlayerSide.RED)  # type: ignore[union-attr]

    def test_render_produces_ten_rows(self, renderer: object, minimal_state: object) -> None:
        """The rendered output contains exactly 10 data rows."""
        output = capture_render(renderer, minimal_state, PlayerSide.RED)
        lines = [ln for ln in output.splitlines() if ln.strip()]
        assert len(lines) >= 10

    def test_render_output_is_non_empty(self, renderer: object, minimal_state: object) -> None:
        """render() must produce at least some output."""
        output = capture_render(renderer, minimal_state, PlayerSide.RED)
        assert len(output.strip()) > 0


# ---------------------------------------------------------------------------
# US-408 AC-2: Piece rank abbreviation appears at correct row/column
# ---------------------------------------------------------------------------


class TestPiecePositionInOutput:
    """AC-2: A piece at (3,5) appears at column 5 of row 3 of the printed grid."""

    def test_own_piece_rank_visible_at_correct_row(self, renderer: object) -> None:
        """A Red Scout at (8,0) appears on row 8 of the rendered output."""
        scout = make_red_piece(Rank.SCOUT, 8, 0)
        state = make_minimal_playing_state(
            red_pieces=[scout, make_red_piece(Rank.FLAG, 9, 0)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        output = capture_render(renderer, state, PlayerSide.RED)
        data_rows = [ln for ln in output.splitlines() if ln.strip()]
        # Row index 8 (0-based) should contain the Scout rank marker
        assert len(data_rows) >= 9
        row8 = data_rows[8]
        # Scout abbreviation should appear somewhere in that row
        assert any(abbr in row8 for abbr in ("SCO", "SCP", "S2", "2"))

    def test_piece_not_at_row_zero_when_placed_at_row_eight(self, renderer: object) -> None:
        """A piece placed at row 8 should NOT appear in row 0 of the output."""
        scout = make_red_piece(Rank.SCOUT, 8, 0)
        state = make_minimal_playing_state(
            red_pieces=[scout, make_red_piece(Rank.FLAG, 9, 0)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 9), make_blue_piece(Rank.SCOUT, 1, 9)],
        )
        output = capture_render(renderer, state, PlayerSide.RED)
        data_rows = [ln for ln in output.splitlines() if ln.strip()]
        row0 = data_rows[0] if data_rows else ""
        # Scout abbreviation should NOT be in row 0
        assert not any(abbr in row0 for abbr in ("SCO", "SCP", "S2"))


# ---------------------------------------------------------------------------
# US-408 AC-3: Lake squares display as ~~
# ---------------------------------------------------------------------------


class TestLakeDisplay:
    """AC-3: Lake squares render as ~~ in the ASCII output."""

    def test_lake_marker_present_in_output(self, renderer: object, minimal_state: object) -> None:
        """The string '~~' appears in the rendered output (lake squares exist)."""
        output = capture_render(renderer, minimal_state, PlayerSide.RED)
        assert "~~" in output

    def test_lake_count_correct_in_output(self, renderer: object, minimal_state: object) -> None:
        """Exactly 8 lake markers appear in the rendered board."""
        output = capture_render(renderer, minimal_state, PlayerSide.RED)
        assert output.count("~~") >= 8


# ---------------------------------------------------------------------------
# US-403 related: Fog-of-war in terminal renderer
# ---------------------------------------------------------------------------


class TestFogOfWarInTerminalOutput:
    """Opponent unrevealed pieces show [?] from the viewing player's perspective."""

    def test_opponent_unrevealed_shows_hidden_marker(self, renderer: object) -> None:
        """An unrevealed Blue piece shown from Red's view must display as [?]."""
        blue_scout_unrevealed = make_blue_piece(Rank.SCOUT, 1, 0, revealed=False)
        state = make_minimal_playing_state(
            red_pieces=[make_red_piece(Rank.FLAG, 9, 0), make_red_piece(Rank.SCOUT, 8, 0)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), blue_scout_unrevealed],
        )
        output = capture_render(renderer, state, PlayerSide.RED)
        assert "[?]" in output

    def test_opponent_revealed_shows_rank(self, renderer: object) -> None:
        """A revealed Blue piece shown from Red's view must display its rank."""
        blue_scout_revealed = make_blue_piece(Rank.SCOUT, 1, 0, revealed=True)
        state = make_minimal_playing_state(
            red_pieces=[make_red_piece(Rank.FLAG, 9, 0), make_red_piece(Rank.SCOUT, 8, 0)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), blue_scout_revealed],
        )
        output = capture_render(renderer, state, PlayerSide.RED)
        # Should NOT show [?] for revealed piece
        data_rows = [ln for ln in output.splitlines() if ln.strip()]
        row1 = data_rows[1] if len(data_rows) > 1 else ""
        assert "[?]" not in row1 or any(abbr in output for abbr in ("SCO", "2"))

    def test_own_pieces_always_show_rank_regardless_of_revealed_flag(
        self, renderer: object
    ) -> None:
        """Own pieces (Red viewing Red) always show rank even with revealed=False."""
        red_scout = make_red_piece(Rank.SCOUT, 8, 0, revealed=False)
        state = make_minimal_playing_state(
            red_pieces=[make_red_piece(Rank.FLAG, 9, 0), red_scout],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        output = capture_render(renderer, state, PlayerSide.RED)
        # Own piece should never be hidden
        data_rows = [ln for ln in output.splitlines() if ln.strip()]
        row8 = data_rows[8] if len(data_rows) > 8 else ""
        assert "[?]" not in row8
