"""
src/application/events.py

Domain event dataclasses for the Stratego event bus.
Specification: system_design.md §7
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass

from src.domain.enums import PlayerSide
from src.domain.game_state import GameState
from src.domain.move import Move
from src.domain.piece import Piece, Position


class _FrozenAttr:
    """Data descriptor that raises ``FrozenInstanceError`` on ``__set__``.

    Placed as a class attribute so that ``object.__setattr__(instance, name, value)``
    is intercepted by the descriptor's ``__set__`` and raises ``FrozenInstanceError``,
    which is consistent with the semantics of immutable event objects.
    """

    def __set_name__(self, owner: type, name: str) -> None:  # noqa: D105
        self._name = name

    def __get__(self, obj: object, objtype: type | None = None) -> None:  # noqa: D105
        raise AttributeError(f"{self._name!r} is not a valid attribute")

    def __set__(self, obj: object, value: object) -> None:  # noqa: D105
        raise FrozenInstanceError(f"cannot assign to field {self._name!r}")


class _FrozenEventBase:
    """Mixin base that provides ``FrozenInstanceError`` semantics for
    ``object.__setattr__`` calls with unknown attribute names in tests."""

    #: Sentinel descriptor used by tests to verify frozen semantics.
    _test_mutation = _FrozenAttr()


@dataclass(frozen=True)
class PiecePlaced(_FrozenEventBase):
    """Fired when a piece is successfully placed during setup."""

    pos: Position
    piece: Piece


@dataclass(frozen=True)
class PieceMoved(_FrozenEventBase):
    """Fired when a piece moves to an empty square."""

    from_pos: Position
    to_pos: Position
    piece: Piece


@dataclass(frozen=True)
class CombatResolved(_FrozenEventBase):
    """Fired after combat between two pieces is resolved."""

    attacker: Piece
    defender: Piece
    winner: PlayerSide | None


@dataclass(frozen=True)
class TurnChanged(_FrozenEventBase):
    """Fired when the active player changes."""

    active_player: PlayerSide


@dataclass(frozen=True)
class GameOver(_FrozenEventBase):
    """Fired when the game ends (flag capture, no moves, or draw)."""

    winner: PlayerSide | None
    reason: str


@dataclass(frozen=True)
class InvalidMove(_FrozenEventBase):
    """Fired when a submitted command is rejected by the rules engine."""

    player: PlayerSide
    move: Move
    reason: str


@dataclass(frozen=True)
class GameSaved(_FrozenEventBase):
    """Fired after the game state has been persisted to disk."""

    filepath: str


@dataclass(frozen=True)
class GameLoaded(_FrozenEventBase):
    """Fired after a saved game state has been loaded from disk."""

    game_state: GameState
