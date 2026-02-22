"""
test_fog_of_war.py — Unit tests for fog-of-war logic in the presentation layer.

Epic: EPIC-4 | User Story: US-403
Covers acceptance criteria: AC-1, AC-2, AC-3, AC-4
Specification: game_components.md §3.2
"""
from __future__ import annotations

from unittest.mock import MagicMock

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
    from src.presentation.pygame_renderer import PygameRenderer
except ImportError:
    PygameRenderer = None  # type: ignore[assignment, misc]

try:
    from src.presentation.sprite_manager import SpriteManager
except ImportError:
    SpriteManager = None  # type: ignore[assignment, misc]

try:
    from src.presentation.terminal_renderer import TerminalRenderer
except ImportError:
    TerminalRenderer = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    PygameRenderer is None and TerminalRenderer is None,
    reason="Presentation renderer(s) not implemented yet",
    strict=False,
)


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_screen() -> MagicMock:
    surface = MagicMock()
    surface.get_width = MagicMock(return_value=1024)
    surface.get_height = MagicMock(return_value=768)
    surface.blit = MagicMock()
    surface.fill = MagicMock()
    return surface


@pytest.fixture
def mock_sprite_manager() -> MagicMock:
    """SpriteManager mock: hidden_surface is distinct from any rank surface."""
    sm = MagicMock()
    rank_surface = MagicMock(name="rank_surface")
    hidden_surface = MagicMock(name="hidden_surface")
    sm.get_surface = MagicMock(
        side_effect=lambda rank, owner, revealed: (
            hidden_surface if not revealed else rank_surface
        )
    )
    sm.hidden_surface = hidden_surface
    sm.rank_surface = rank_surface
    sm.lake_surface = MagicMock(name="lake_surface")
    sm.empty_surface = MagicMock(name="empty_surface")
    return sm


@pytest.fixture
def pygame_renderer(mock_screen: MagicMock, mock_sprite_manager: MagicMock) -> object:
    return PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)


# ---------------------------------------------------------------------------
# US-403 AC-1: Unrevealed opponent pieces are hidden from the viewing player
# ---------------------------------------------------------------------------


class TestUnrevealedOpponentPiecesAreHidden:
    """AC-1: An opponent's unrevealed piece shows as a face-down sprite."""

    def test_unrevealed_blue_piece_uses_hidden_surface_for_red_viewer(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
    ) -> None:
        """Hidden surface is used when rendering Blue's unrevealed piece from Red's view."""
        blue_spy_unrevealed = make_blue_piece(Rank.SPY, 2, 3, revealed=False)
        state = make_minimal_playing_state(
            red_pieces=[make_red_piece(Rank.FLAG, 9, 0), make_red_piece(Rank.SCOUT, 8, 0)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), blue_spy_unrevealed],
        )
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(state, PlayerSide.RED)

        # get_surface must have been called with revealed=False for the unrevealed piece
        calls = mock_sprite_manager.get_surface.call_args_list
        hidden_calls = [
            c for c in calls
            if c.kwargs.get("revealed") is False or (c.args and len(c.args) >= 3 and c.args[2] is False)
        ]
        assert len(hidden_calls) >= 1

    def test_unrevealed_red_piece_uses_hidden_surface_for_blue_viewer(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
    ) -> None:
        """Hidden surface is used when rendering Red's unrevealed piece from Blue's view."""
        red_marshal_unrevealed = make_red_piece(Rank.MARSHAL, 7, 5, revealed=False)
        state = make_minimal_playing_state(
            red_pieces=[make_red_piece(Rank.FLAG, 9, 0), red_marshal_unrevealed],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(state, PlayerSide.BLUE)

        calls = mock_sprite_manager.get_surface.call_args_list
        hidden_calls = [
            c for c in calls
            if c.kwargs.get("revealed") is False or (c.args and len(c.args) >= 3 and c.args[2] is False)
        ]
        assert len(hidden_calls) >= 1


# ---------------------------------------------------------------------------
# US-403 AC-2: Revealed opponent pieces show rank
# ---------------------------------------------------------------------------


class TestRevealedOpponentPiecesShowRank:
    """AC-2: An opponent's revealed (post-combat) piece shows its rank."""

    def test_revealed_blue_piece_uses_rank_surface_for_red_viewer(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
    ) -> None:
        """Rank surface (not hidden) is used for a revealed opponent piece."""
        blue_captain_revealed = make_blue_piece(Rank.CAPTAIN, 2, 3, revealed=True)
        state = make_minimal_playing_state(
            red_pieces=[make_red_piece(Rank.FLAG, 9, 0), make_red_piece(Rank.SCOUT, 8, 0)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), blue_captain_revealed],
        )
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(state, PlayerSide.RED)

        calls = mock_sprite_manager.get_surface.call_args_list
        rank_calls = [
            c for c in calls
            if c.kwargs.get("revealed") is True or (c.args and len(c.args) >= 3 and c.args[2] is True)
        ]
        assert len(rank_calls) >= 1


# ---------------------------------------------------------------------------
# US-403 AC-3: Own pieces always show rank
# ---------------------------------------------------------------------------


class TestOwnPiecesAlwaysShowRank:
    """AC-3: The viewing player's own pieces always show their rank."""

    def test_own_unrevealed_piece_still_uses_rank_surface(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
    ) -> None:
        """Red's own piece with revealed=False is still shown with its rank to Red."""
        red_scout_unrevealed = make_red_piece(Rank.SCOUT, 8, 0, revealed=False)
        state = make_minimal_playing_state(
            red_pieces=[make_red_piece(Rank.FLAG, 9, 0), red_scout_unrevealed],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(state, PlayerSide.RED)

        # For Red's own pieces the renderer must pass revealed=True (or treat them as visible)
        # regardless of the piece.revealed flag
        rank_surface = mock_sprite_manager.rank_surface
        blit_surfaces = [c.args[0] for c in mock_screen.blit.call_args_list if c.args]
        assert rank_surface in blit_surfaces


# ---------------------------------------------------------------------------
# US-403 AC-4: From Blue's perspective, Red's unrevealed pieces are hidden
# ---------------------------------------------------------------------------


class TestBluePerspectiveFogOfWar:
    """AC-4: From Blue's perspective, Red's unrevealed pieces show no rank."""

    def test_red_unrevealed_piece_hidden_from_blue_viewer(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
    ) -> None:
        """Red's unrevealed piece uses hidden surface when viewed by Blue."""
        red_general_unrevealed = make_red_piece(Rank.GENERAL, 7, 5, revealed=False)
        state = make_minimal_playing_state(
            red_pieces=[make_red_piece(Rank.FLAG, 9, 0), red_general_unrevealed],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(state, PlayerSide.BLUE)

        hidden_surface = mock_sprite_manager.hidden_surface
        blit_surfaces = [c.args[0] for c in mock_screen.blit.call_args_list if c.args]
        assert hidden_surface in blit_surfaces

    def test_fog_of_war_applied_in_renderer_not_domain(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
    ) -> None:
        """piece.revealed flag is NOT modified in the domain layer by the renderer."""
        red_scout = make_red_piece(Rank.SCOUT, 8, 0, revealed=False)
        state = make_minimal_playing_state(
            red_pieces=[make_red_piece(Rank.FLAG, 9, 0), red_scout],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        original_revealed = red_scout.revealed
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(state, PlayerSide.BLUE)
        # The original piece must be unchanged — domain is immutable.
        assert red_scout.revealed == original_revealed


# ---------------------------------------------------------------------------
# Terminal renderer fog-of-war (US-403 linked to US-408)
# ---------------------------------------------------------------------------


class TestTerminalRendererFogOfWar:
    """Fog-of-war in the terminal renderer (headless path)."""

    @pytest.mark.xfail(TerminalRenderer is None, reason="TerminalRenderer not implemented yet", strict=False)
    def test_terminal_renderer_hides_unrevealed_opponent(self) -> None:
        """TerminalRenderer hides unrevealed opponent pieces with [?]."""
        import io
        from contextlib import redirect_stdout

        renderer = TerminalRenderer()
        blue_spy = make_blue_piece(Rank.SPY, 2, 3, revealed=False)
        state = make_minimal_playing_state(
            red_pieces=[make_red_piece(Rank.FLAG, 9, 0), make_red_piece(Rank.SCOUT, 8, 0)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), blue_spy],
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            renderer.render(state, PlayerSide.RED)
        output = buf.getvalue()
        assert "[?]" in output

    @pytest.mark.xfail(TerminalRenderer is None, reason="TerminalRenderer not implemented yet", strict=False)
    def test_terminal_renderer_shows_own_pieces_always(self) -> None:
        """TerminalRenderer shows own (Red) pieces regardless of revealed=False."""
        import io
        from contextlib import redirect_stdout

        renderer = TerminalRenderer()
        red_marshal = make_red_piece(Rank.MARSHAL, 8, 0, revealed=False)
        state = make_minimal_playing_state(
            red_pieces=[make_red_piece(Rank.FLAG, 9, 0), red_marshal],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            renderer.render(state, PlayerSide.RED)
        output = buf.getvalue()
        data_rows = [ln for ln in output.splitlines() if ln.strip()]
        row8 = data_rows[8] if len(data_rows) > 8 else ""
        assert "[?]" not in row8
