"""Test fixtures – re-exports sample game-state factory functions."""

from tests.fixtures.sample_game_states import (
    make_empty_board,
    make_initial_game_state,
    make_playing_state,
)

__all__ = ["make_empty_board", "make_initial_game_state", "make_playing_state"]
