"""
src/domain/game_state.py

Immutable GameState snapshot — the root aggregate of the domain model.
Specification: data_models.md §2 (GameState entity) and §4 (Invariants)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.board import Board
from src.domain.enums import GamePhase, PlayerSide
from src.domain.player import Player


@dataclass(frozen=True)
class CombatRecord:
    """Minimal record of a single combat for history purposes."""

    attacker_rank: str
    defender_rank: str
    outcome: str


@dataclass(frozen=True)
class MoveRecord:
    """An entry in the immutable move history (data_models.md §2)."""

    turn_number: int
    from_pos: tuple[int, int]
    to_pos: tuple[int, int]
    move_type: str
    combat_result: CombatRecord | None = None
    timestamp: float = 0.0


@dataclass(frozen=True)
class GameState:
    """A complete, immutable snapshot of the Stratego game at one point in time.

    Invariants enforced (data_models.md §4):
    - I-1: Positions are in [0,9]×[0,9] (enforced by Position.is_valid).
    - I-2: No two pieces share a Position (enforced by Board).
    - I-3: No piece on a LAKE square (enforced by Board).
    - I-4: FLAG/BOMB never have has_moved=True.
    - I-5: Each player has exactly one FLAG at game start.
    - I-6: active_player alternates after each valid move.
    - I-7: move_history is append-only.
    - I-8: winner is None unless phase == GAME_OVER.
    - I-9: piece.position matches its Board square.
    - I-10: Player.pieces_remaining matches board pieces.
    """

    board: Board
    players: tuple[Player, Player]
    active_player: PlayerSide
    phase: GamePhase
    turn_number: int
    move_history: tuple[MoveRecord, ...] = field(default_factory=tuple)
    winner: PlayerSide | None = None
