"""
src/application/game_controller.py

GameController — routes commands to the domain layer and publishes events.
Specification: system_design.md §4
"""
from __future__ import annotations

import logging
from types import ModuleType
from typing import Any

from src.application.commands import Command, MovePiece, PlacePiece
from src.application.event_bus import EventBus
from src.application.events import (
    CombatResolved,
    GameOver,
    InvalidMove,
    PieceMoved,
    PiecePlaced,
    TurnChanged,
)
from src.domain.enums import CombatOutcome, GamePhase, MoveType, Rank
from src.domain.game_state import GameState
from src.domain.move import Move
from src.domain.piece import Piece
from src.domain.rules_engine import RulesViolationError, ValidationResult

logger = logging.getLogger(__name__)


class GameController:
    """Routes player commands to the domain layer and broadcasts domain events.

    The controller holds the authoritative current ``GameState`` and is the
    single mutation point during a game session.  All state changes go through
    ``submit_command``; no other component should write directly to the domain.
    """

    def __init__(
        self,
        initial_state: GameState,
        event_bus: EventBus,
        rules_engine: ModuleType,
    ) -> None:
        """Initialise the controller.

        Args:
            initial_state: The starting ``GameState`` snapshot.
            event_bus: The shared ``EventBus`` used to broadcast domain events.
            rules_engine: The ``src.domain.rules_engine`` module (injected for
                testability).
        """
        self._state = initial_state
        self._event_bus = event_bus
        self._rules_engine = rules_engine

    @property
    def current_state(self) -> GameState:
        """Return the current (immutable) ``GameState`` snapshot."""
        return self._state

    # ------------------------------------------------------------------
    # Command dispatch
    # ------------------------------------------------------------------

    def submit_command(self, cmd: Command) -> None:
        """Validate and apply *cmd*, then publish the appropriate domain events.

        Args:
            cmd: A ``PlacePiece`` or ``MovePiece`` command instance.
        """
        if isinstance(cmd, PlacePiece):
            self._handle_place_piece(cmd)
        elif isinstance(cmd, MovePiece):
            self._handle_move_piece(cmd)
        else:
            logger.warning("GameController: unrecognised command type %r", type(cmd))

    # ------------------------------------------------------------------
    # Internal handlers
    # ------------------------------------------------------------------

    def _handle_place_piece(self, cmd: PlacePiece) -> None:
        """Validate and apply a placement command."""
        result = self._rules_engine.validate_placement(self._state, cmd.piece, cmd.pos)
        if result != ValidationResult.OK:
            dummy_move = Move(
                piece=cmd.piece,
                from_pos=cmd.pos,
                to_pos=cmd.pos,
                move_type=MoveType.MOVE,
            )
            self._event_bus.publish(
                InvalidMove(
                    player=cmd.piece.owner,
                    move=dummy_move,
                    reason="Placement rejected by rules engine",
                )
            )
            return
        try:
            new_state = self._rules_engine.apply_placement(self._state, cmd.piece, cmd.pos)
        except RulesViolationError as exc:
            dummy_move = Move(
                piece=cmd.piece,
                from_pos=cmd.pos,
                to_pos=cmd.pos,
                move_type=MoveType.MOVE,
            )
            self._event_bus.publish(
                InvalidMove(
                    player=cmd.piece.owner,
                    move=dummy_move,
                    reason=str(exc),
                )
            )
            return
        self._state = new_state
        placed_piece = self._state.board.get_square(cmd.pos).piece
        assert placed_piece is not None
        self._event_bus.publish(PiecePlaced(pos=cmd.pos, piece=placed_piece))

    def _handle_move_piece(self, cmd: MovePiece) -> None:
        """Validate and apply a move command."""
        # Look up the piece that is being moved.
        from_sq = self._state.board.get_square(cmd.from_pos)
        if from_sq.piece is None:
            dummy_move = Move(
                piece=Piece(
                    rank=Rank.SCOUT,
                    owner=self._state.active_player,
                    revealed=False,
                    has_moved=False,
                    position=cmd.from_pos,
                ),
                from_pos=cmd.from_pos,
                to_pos=cmd.to_pos,
                move_type=MoveType.MOVE,
            )
            self._event_bus.publish(
                InvalidMove(
                    player=self._state.active_player,
                    move=dummy_move,
                    reason="No piece at source square",
                )
            )
            return

        piece = from_sq.piece

        # Check the destination to detect combat.
        dest_sq = self._state.board.get_square(cmd.to_pos)
        is_attack = dest_sq.piece is not None and dest_sq.piece.owner != piece.owner
        defender_before: Piece | None = dest_sq.piece if is_attack else None

        move_type = MoveType.ATTACK if is_attack else MoveType.MOVE
        move = Move(
            piece=piece,
            from_pos=cmd.from_pos,
            to_pos=cmd.to_pos,
            move_type=move_type,
        )

        try:
            result = self._rules_engine.validate_move(self._state, move)
        except RulesViolationError as exc:
            self._event_bus.publish(
                InvalidMove(
                    player=piece.owner,
                    move=move,
                    reason=str(exc),
                )
            )
            return

        if result != ValidationResult.OK:
            self._event_bus.publish(
                InvalidMove(
                    player=piece.owner,
                    move=move,
                    reason="Move rejected by rules engine",
                )
            )
            return

        try:
            new_state = self._rules_engine.apply_move(self._state, move)
        except RulesViolationError as exc:
            self._event_bus.publish(
                InvalidMove(
                    player=piece.owner,
                    move=move,
                    reason=str(exc),
                )
            )
            return

        self._state = new_state

        # --- Publish events ---
        if is_attack and defender_before is not None:
            combat_record = new_state.move_history[-1].combat_result
            winner_side = self._resolve_winner(
                piece.owner,
                defender_before.owner,
                combat_record.outcome if combat_record else None,
            )
            self._event_bus.publish(
                CombatResolved(
                    attacker=piece,
                    defender=defender_before,
                    winner=winner_side,
                )
            )
        else:
            moved_piece = new_state.board.get_square(cmd.to_pos).piece
            published_piece = moved_piece if moved_piece is not None else piece
            self._event_bus.publish(
                PieceMoved(
                    from_pos=cmd.from_pos,
                    to_pos=cmd.to_pos,
                    piece=published_piece,
                )
            )

        # Game over?
        if new_state.phase == GamePhase.GAME_OVER:
            reason = (
                "Flag captured"
                if new_state.winner is not None
                else "Draw — turn limit or no moves"
            )
            self._event_bus.publish(
                GameOver(winner=new_state.winner, reason=reason)
            )
        else:
            # Turn changed.
            self._event_bus.publish(TurnChanged(active_player=new_state.active_player))

    @staticmethod
    def _resolve_winner(
        attacker_side: Any,
        defender_side: Any,
        outcome_name: str | None,
    ) -> Any:
        """Map a CombatOutcome name to the winning PlayerSide (or None for draw)."""
        if outcome_name == CombatOutcome.ATTACKER_WINS.name:
            return attacker_side
        if outcome_name == CombatOutcome.DEFENDER_WINS.name:
            return defender_side
        return None
