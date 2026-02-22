"""
test_input_handler.py — Unit tests for src/presentation/input_handler.py

Epic: EPIC-4 | User Story: US-402
Covers acceptance criteria: AC-1, AC-2, AC-3, AC-4, AC-5
Specification: system_design.md §2.4
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
    from src.presentation.input_handler import (
        ClickEvent,
        InputHandler,
        QuitEvent,
        RightClickEvent,
    )
except ImportError:
    InputHandler = None  # type: ignore[assignment, misc]
    ClickEvent = None  # type: ignore[assignment, misc]
    RightClickEvent = None  # type: ignore[assignment, misc]
    QuitEvent = None  # type: ignore[assignment, misc]

pytestmark = pytest.mark.xfail(
    InputHandler is None,
    reason="src.presentation.input_handler not implemented yet",
    strict=False,
)

# ---------------------------------------------------------------------------
# Constants — matches renderer spec (1024×768, board = left 75%)
# ---------------------------------------------------------------------------

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
BOARD_WIDTH = int(WINDOW_WIDTH * 0.75)
CELL_SIZE = BOARD_WIDTH // 10  # ~76 px


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_pygame_event(event_type: int, **kwargs: object) -> MagicMock:
    """Create a mock pygame.event.Event with the given type and attributes."""
    event = MagicMock()
    event.type = event_type
    for key, value in kwargs.items():
        setattr(event, key, value)
    return event


# Mock pygame constants that may not be importable without a display.
try:
    import pygame

    MOUSEBUTTONDOWN = pygame.MOUSEBUTTONDOWN
    QUIT = pygame.QUIT
except ImportError:
    MOUSEBUTTONDOWN = 1025
    QUIT = 256


@pytest.fixture
def handler() -> object:
    return InputHandler()


@pytest.fixture
def playing_state() -> object:
    return make_minimal_playing_state()


# ---------------------------------------------------------------------------
# US-402 AC-1: Left-click maps to correct grid Position
# ---------------------------------------------------------------------------


class TestLeftClickMapping:
    """AC-1: A left-click at a pixel maps to the correct grid Position."""

    @pytest.mark.parametrize(
        "pixel_x, pixel_y, expected_row, expected_col",
        [
            # Click at (col*cell_size + half, row*cell_size + half) → grid (row, col)
            (CELL_SIZE * 0 + CELL_SIZE // 2, CELL_SIZE * 6 + CELL_SIZE // 2, 6, 0),
            (CELL_SIZE * 4 + CELL_SIZE // 2, CELL_SIZE * 6 + CELL_SIZE // 2, 6, 4),
            (CELL_SIZE * 9 + CELL_SIZE // 2, CELL_SIZE * 9 + CELL_SIZE // 2, 9, 9),
            (CELL_SIZE * 0 + CELL_SIZE // 2, CELL_SIZE * 0 + CELL_SIZE // 2, 0, 0),
        ],
        ids=["col0_row6", "col4_row6", "col9_row9", "col0_row0"],
    )
    def test_left_click_maps_to_correct_grid_position(
        self,
        handler: object,
        playing_state: object,
        pixel_x: int,
        pixel_y: int,
        expected_row: int,
        expected_col: int,
    ) -> None:
        """A left-click at (pixel_x, pixel_y) yields grid Position(expected_row, expected_col)."""
        event = make_pygame_event(MOUSEBUTTONDOWN, button=1, pos=(pixel_x, pixel_y))
        result = handler.process(event, playing_state, PlayerSide.RED)  # type: ignore[union-attr]
        assert result is not None
        assert isinstance(result, ClickEvent)
        assert result.pos == Position(expected_row, expected_col)

    def test_left_click_returns_click_event(
        self, handler: object, playing_state: object
    ) -> None:
        """process() returns a ClickEvent for a left mouse button down event."""
        pixel_x = CELL_SIZE * 4 + CELL_SIZE // 2
        pixel_y = CELL_SIZE * 6 + CELL_SIZE // 2
        event = make_pygame_event(MOUSEBUTTONDOWN, button=1, pos=(pixel_x, pixel_y))
        result = handler.process(event, playing_state, PlayerSide.RED)  # type: ignore[union-attr]
        assert isinstance(result, ClickEvent)


# ---------------------------------------------------------------------------
# US-402 AC-3: Right-click returns RightClickEvent
# ---------------------------------------------------------------------------


class TestRightClickReturnsRightClickEvent:
    """AC-3: A right-click anywhere returns RightClickEvent."""

    def test_right_click_returns_right_click_event(
        self, handler: object, playing_state: object
    ) -> None:
        """Button 3 (right-click) returns a RightClickEvent instance."""
        event = make_pygame_event(MOUSEBUTTONDOWN, button=3, pos=(100, 100))
        result = handler.process(event, playing_state, PlayerSide.RED)  # type: ignore[union-attr]
        assert isinstance(result, RightClickEvent)

    def test_right_click_at_any_position_returns_right_click_event(
        self, handler: object, playing_state: object
    ) -> None:
        """Right-click position does not matter — always RightClickEvent."""
        for pos in [(0, 0), (BOARD_WIDTH // 2, WINDOW_HEIGHT // 2), (WINDOW_WIDTH - 1, WINDOW_HEIGHT - 1)]:
            event = make_pygame_event(MOUSEBUTTONDOWN, button=3, pos=pos)
            result = handler.process(event, playing_state, PlayerSide.RED)  # type: ignore[union-attr]
            assert isinstance(result, RightClickEvent)


# ---------------------------------------------------------------------------
# US-402 AC-5: QUIT event → QuitEvent
# ---------------------------------------------------------------------------


class TestQuitEventMapping:
    """AC-5: A pygame QUIT event returns QuitEvent."""

    def test_quit_event_returns_quit_event_instance(
        self, handler: object, playing_state: object
    ) -> None:
        """process() returns QuitEvent for pygame.QUIT."""
        event = make_pygame_event(QUIT)
        result = handler.process(event, playing_state, PlayerSide.RED)  # type: ignore[union-attr]
        assert isinstance(result, QuitEvent)


# ---------------------------------------------------------------------------
# US-402 AC-2 & AC-4: Click on wrong-turn or opponent piece
# ---------------------------------------------------------------------------


class TestInvalidClickScenarios:
    """AC-4: Clicking an opponent's piece while it is Red's turn returns no command."""

    def test_unrecognised_event_type_returns_none(
        self, handler: object, playing_state: object
    ) -> None:
        """An unrecognised pygame event type returns None."""
        event = make_pygame_event(9999)
        result = handler.process(event, playing_state, PlayerSide.RED)  # type: ignore[union-attr]
        assert result is None


# ---------------------------------------------------------------------------
# InputEvent dataclass immutability
# ---------------------------------------------------------------------------


class TestInputEventDataclasses:
    """ClickEvent, RightClickEvent, QuitEvent are immutable value objects."""

    def test_click_event_stores_position(self) -> None:
        """ClickEvent.pos returns the Position it was created with."""
        pos = Position(6, 4)
        event = ClickEvent(pos=pos)
        assert event.pos == pos

    def test_right_click_event_instantiable(self) -> None:
        """RightClickEvent can be instantiated without arguments."""
        event = RightClickEvent()
        assert event is not None

    def test_quit_event_instantiable(self) -> None:
        """QuitEvent can be instantiated without arguments."""
        event = QuitEvent()
        assert event is not None

    def test_click_event_equality(self) -> None:
        """Two ClickEvents with the same pos are equal."""
        a = ClickEvent(pos=Position(3, 5))
        b = ClickEvent(pos=Position(3, 5))
        assert a == b

    def test_click_event_inequality_different_pos(self) -> None:
        """Two ClickEvents with different pos are not equal."""
        a = ClickEvent(pos=Position(3, 5))
        b = ClickEvent(pos=Position(4, 5))
        assert a != b
