"""
src/Tests/conftest.py

Root conftest.py — shared pytest fixtures available to all test modules.
"""
from __future__ import annotations

import pytest

from src.domain.board import Board
from src.domain.game_state import GameState
from src.Tests.fixtures.sample_game_states import (
    make_empty_setup_state,
    make_minimal_playing_state,
)


@pytest.fixture
def empty_board() -> Board:
    """A freshly created, piece-free 10×10 board with lake squares."""
    return Board.create_empty()


@pytest.fixture
def empty_setup_state() -> GameState:
    """A GameState in SETUP phase with an empty board."""
    return make_empty_setup_state()


@pytest.fixture
def minimal_playing_state() -> GameState:
    """A minimal PLAYING GameState — two pieces per side (Flag + Scout)."""
    return make_minimal_playing_state()
