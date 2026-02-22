"""
src/presentation/input_handler.py

InputHandler — converts pygame events into domain InputEvent objects.
Specification: system_design.md §2.4
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.domain.enums import PlayerSide
from src.domain.game_state import GameState
from src.domain.piece import Position

# Layout constants — must match pygame_renderer.py.
_WINDOW_WIDTH: int = 1024
_WINDOW_HEIGHT: int = 768
_BOARD_FRACTION: float = 0.75
_BOARD_COLS: int = 10
_BOARD_ROWS: int = 10

# Lazy import of pygame constants so the module works without a display.
try:
    import pygame as _pygame

    _MOUSEBUTTONDOWN = _pygame.MOUSEBUTTONDOWN
    _QUIT = _pygame.QUIT
except ImportError:
    _MOUSEBUTTONDOWN = 1025
    _QUIT = 256


# ---------------------------------------------------------------------------
# InputEvent value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClickEvent:
    """A left-click mapped to a board grid position."""

    pos: Position


@dataclass(frozen=True)
class RightClickEvent:
    """A right-click anywhere on the window."""


@dataclass(frozen=True)
class QuitEvent:
    """The user has requested to close the application."""


InputEvent = ClickEvent | RightClickEvent | QuitEvent


# ---------------------------------------------------------------------------
# InputHandler
# ---------------------------------------------------------------------------


class InputHandler:
    """Translates raw pygame events into ``InputEvent`` objects.

    This class only converts events to grid positions; higher-level
    click-to-command logic lives in the screen classes (e.g.
    ``PlayingScreen``).
    """

    def __init__(
        self,
        window_width: int = _WINDOW_WIDTH,
        window_height: int = _WINDOW_HEIGHT,
        board_fraction: float = _BOARD_FRACTION,
    ) -> None:
        """Initialise the handler with layout parameters.

        Args:
            window_width: Total window width in pixels.
            window_height: Total window height in pixels.
            board_fraction: Fraction of window width occupied by the board.
        """
        self._board_width = int(window_width * board_fraction)
        self._cell_w = self._board_width // _BOARD_COLS
        self._cell_h = window_height // _BOARD_ROWS

    def process(
        self,
        pygame_event: Any,
        current_state: GameState,  # noqa: ARG002 — reserved for future use
        viewing_player: PlayerSide,  # noqa: ARG002 — reserved for future use
    ) -> InputEvent | None:
        """Convert *pygame_event* to an ``InputEvent`` or ``None``.

        Args:
            pygame_event: A pygame event object.
            current_state: The current ``GameState`` (available for context).
            viewing_player: The active viewing player (available for context).

        Returns:
            An ``InputEvent`` subclass instance, or ``None`` for unrecognised
            event types.
        """
        event_type = pygame_event.type

        if event_type == _QUIT:
            return QuitEvent()

        if event_type == _MOUSEBUTTONDOWN:
            button = getattr(pygame_event, "button", None)
            if button == 3:
                return RightClickEvent()
            if button == 1:
                px, py = pygame_event.pos
                col = px // self._cell_w
                row = py // self._cell_h
                # Clamp to valid board coordinates.
                col = max(0, min(_BOARD_COLS - 1, col))
                row = max(0, min(_BOARD_ROWS - 1, row))
                return ClickEvent(pos=Position(row, col))

        return None
