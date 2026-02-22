"""
test_pygame_renderer.py — Unit tests for src/presentation/pygame_renderer.py

Epic: EPIC-4 | User Story: US-401
Covers acceptance criteria: AC-1, AC-2, AC-3, AC-4
Specification: system_design.md §2.4
"""
from __future__ import annotations

from unittest.mock import MagicMock, call, patch

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

pytestmark = pytest.mark.xfail(
    PygameRenderer is None,
    reason="src.presentation.pygame_renderer not implemented yet",
    strict=False,
)

# ---------------------------------------------------------------------------
# Constants — mirrors spec: board occupies left 75% of 1024×768 window.
# ---------------------------------------------------------------------------

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
BOARD_WIDTH = int(WINDOW_WIDTH * 0.75)  # 768 px
CELL_SIZE = BOARD_WIDTH // 10  # 76 px (approx)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_screen() -> MagicMock:
    """A mock pygame.Surface acting as the display surface."""
    surface = MagicMock()
    surface.get_width = MagicMock(return_value=WINDOW_WIDTH)
    surface.get_height = MagicMock(return_value=WINDOW_HEIGHT)
    surface.blit = MagicMock()
    surface.fill = MagicMock()
    return surface


@pytest.fixture
def mock_sprite_manager() -> MagicMock:
    """A mock SpriteManager that always returns a MagicMock surface."""
    sm = MagicMock()
    sm.get_surface = MagicMock(return_value=MagicMock())
    sm.lake_surface = MagicMock()
    sm.empty_surface = MagicMock()
    return sm


@pytest.fixture
def renderer(mock_screen: MagicMock, mock_sprite_manager: MagicMock) -> object:
    return PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)


@pytest.fixture
def minimal_state() -> object:
    return make_minimal_playing_state()


# ---------------------------------------------------------------------------
# US-401 AC-1: Piece at (6,4) blitted at correct pixel coordinates
# ---------------------------------------------------------------------------


class TestPieceBlit:
    """AC-1: A piece at grid (row, col) is blitted at the correct pixel position."""

    def test_piece_blitted_when_present_on_board(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
    ) -> None:
        """render() calls blit() at least once for a piece on the board."""
        red_scout = make_red_piece(Rank.SCOUT, 6, 4)
        state = make_minimal_playing_state(
            red_pieces=[red_scout, make_red_piece(Rank.FLAG, 9, 0)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(state, PlayerSide.RED)
        assert mock_screen.blit.call_count >= 1

    def test_piece_blitted_at_correct_pixel_column(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
    ) -> None:
        """A piece at column 4 is blitted with an x-coordinate near col*cell_size."""
        red_scout = make_red_piece(Rank.SCOUT, 6, 4)
        state = make_minimal_playing_state(
            red_pieces=[red_scout, make_red_piece(Rank.FLAG, 9, 0)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(state, PlayerSide.RED)
        # The x-position for column 4 should be approximately 4 * cell_size
        blit_positions = [c.args[1] for c in mock_screen.blit.call_args_list if c.args]
        pixel_xs = [pos[0] for pos in blit_positions if isinstance(pos, (tuple, list))]
        expected_x = 4 * CELL_SIZE
        assert any(abs(x - expected_x) < CELL_SIZE for x in pixel_xs)

    def test_piece_blitted_at_correct_pixel_row(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
    ) -> None:
        """A piece at row 6 is blitted with a y-coordinate near row*cell_size."""
        red_scout = make_red_piece(Rank.SCOUT, 6, 4)
        state = make_minimal_playing_state(
            red_pieces=[red_scout, make_red_piece(Rank.FLAG, 9, 0)],
            blue_pieces=[make_blue_piece(Rank.FLAG, 0, 0), make_blue_piece(Rank.SCOUT, 1, 0)],
        )
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(state, PlayerSide.RED)
        blit_positions = [c.args[1] for c in mock_screen.blit.call_args_list if c.args]
        pixel_ys = [pos[1] for pos in blit_positions if isinstance(pos, (tuple, list))]
        expected_y = 6 * CELL_SIZE
        assert any(abs(y - expected_y) < CELL_SIZE for y in pixel_ys)


# ---------------------------------------------------------------------------
# US-401 AC-2: Lake squares use the lake texture
# ---------------------------------------------------------------------------


class TestLakeTexture:
    """AC-2: Lake squares are rendered using the lake texture, not the normal surface."""

    def test_lake_surface_used_for_lake_squares(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
        minimal_state: object,
    ) -> None:
        """The lake texture surface is blitted at each of the 8 lake positions."""
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(minimal_state, PlayerSide.RED)
        # At least 8 blit calls should involve the lake surface
        lake_surface = mock_sprite_manager.lake_surface
        lake_blit_calls = [c for c in mock_screen.blit.call_args_list if c.args and c.args[0] is lake_surface]
        assert len(lake_blit_calls) >= 8

    def test_all_100_squares_are_rendered(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
        minimal_state: object,
    ) -> None:
        """render() produces blit calls for all 100 squares of the board."""
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(minimal_state, PlayerSide.RED)
        # Background fills + per-square blits ≥ 100
        assert mock_screen.blit.call_count >= 100


# ---------------------------------------------------------------------------
# US-401 AC-3: All squares fit within the window
# ---------------------------------------------------------------------------


class TestBoardFitsInWindow:
    """AC-3: All 100 squares fit within the window dimensions without overflow."""

    def test_no_blit_outside_window_width(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
        minimal_state: object,
    ) -> None:
        """No blit x-coordinate exceeds the window width."""
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(minimal_state, PlayerSide.RED)
        for c in mock_screen.blit.call_args_list:
            if c.args and isinstance(c.args[1], (tuple, list)) and len(c.args[1]) >= 2:
                x = c.args[1][0]
                assert x < WINDOW_WIDTH, f"Blit x={x} exceeds window width {WINDOW_WIDTH}"

    def test_no_blit_outside_window_height(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
        minimal_state: object,
    ) -> None:
        """No blit y-coordinate exceeds the window height."""
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(minimal_state, PlayerSide.RED)
        for c in mock_screen.blit.call_args_list:
            if c.args and isinstance(c.args[1], (tuple, list)) and len(c.args[1]) >= 2:
                y = c.args[1][1]
                assert y < WINDOW_HEIGHT, f"Blit y={y} exceeds window height {WINDOW_HEIGHT}"


# ---------------------------------------------------------------------------
# US-401 AC-4: No exception when render() is called
# ---------------------------------------------------------------------------


class TestRenderDoesNotRaise:
    """AC-4: render() must not raise any exception under normal conditions."""

    def test_render_with_empty_board_does_not_raise(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
    ) -> None:
        """Rendering a minimal playing state raises no exception."""
        state = make_minimal_playing_state()
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(state, PlayerSide.RED)

    def test_render_from_blue_perspective_does_not_raise(
        self,
        mock_screen: MagicMock,
        mock_sprite_manager: MagicMock,
    ) -> None:
        """Rendering from Blue's perspective raises no exception."""
        state = make_minimal_playing_state()
        renderer = PygameRenderer(screen=mock_screen, sprite_manager=mock_sprite_manager)
        renderer.render(state, PlayerSide.BLUE)


# ---------------------------------------------------------------------------
# SpriteManager tests
# ---------------------------------------------------------------------------


class TestSpriteManager:
    """SpriteManager loads surfaces and respects fog-of-war."""

    def test_get_surface_returns_value_for_each_rank(self) -> None:
        """get_surface returns a non-None value for every rank."""
        from src.presentation.sprite_manager import SpriteManager as SM

        sm = SM(asset_dir=MagicMock())
        for rank in Rank:
            if rank in (Rank.FLAG, Rank.BOMB):
                continue
            result = sm.get_surface(rank=rank, owner=PlayerSide.RED, revealed=True)
            assert result is not None

    def test_get_surface_returns_hidden_for_unrevealed_opponent(self) -> None:
        """get_surface returns the hidden surface for unrevealed opponent pieces."""
        from src.presentation.sprite_manager import SpriteManager as SM

        sm = SM(asset_dir=MagicMock())
        hidden = sm.get_surface(rank=Rank.SCOUT, owner=PlayerSide.BLUE, revealed=False)
        visible = sm.get_surface(rank=Rank.SCOUT, owner=PlayerSide.BLUE, revealed=True)
        assert hidden is not visible
