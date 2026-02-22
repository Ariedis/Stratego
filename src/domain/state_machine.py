"""Game phase state machine for Stratego lifecycle transitions."""

from __future__ import annotations

import dataclasses

from src.domain.enums import GamePhase
from src.domain.game_state import GameState

# Allowed transitions: {current_phase: set_of_valid_next_phases}
_VALID_TRANSITIONS: dict[GamePhase, frozenset[GamePhase]] = {
    GamePhase.MAIN_MENU: frozenset({GamePhase.SETUP, GamePhase.PLAYING}),
    GamePhase.SETUP: frozenset({GamePhase.PLAYING}),
    GamePhase.PLAYING: frozenset({GamePhase.PLAYING, GamePhase.GAME_OVER}),
    GamePhase.GAME_OVER: frozenset({GamePhase.MAIN_MENU}),
}


class InvalidTransitionError(Exception):
    """Raised when a requested phase transition is not permitted."""


def transition(state: GameState, target_phase: GamePhase) -> GameState:
    """Return a new ``GameState`` with *phase* set to *target_phase*.

    Raises :class:`InvalidTransitionError` when the transition from the
    current phase to *target_phase* is not defined in the state machine.
    """
    allowed = _VALID_TRANSITIONS.get(state.phase, frozenset())
    if target_phase not in allowed:
        raise InvalidTransitionError(
            f"Cannot transition from {state.phase} to {target_phase}"
        )
    return dataclasses.replace(state, phase=target_phase)


def is_valid_transition(current: GamePhase, target: GamePhase) -> bool:
    """Return True when the *current* → *target* transition is defined."""
    return target in _VALID_TRANSITIONS.get(current, frozenset())
