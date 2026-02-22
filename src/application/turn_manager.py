"""
src/application/turn_manager.py

TurnManager — dispatches AI moves when it is an AI player's turn.
Specification: system_design.md §2.2, §5
"""
from __future__ import annotations

import logging
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

from src.application.commands import MovePiece
from src.application.event_bus import EventBus
from src.application.events import TurnChanged
from src.domain.enums import PlayerType
from src.domain.move import Move
from src.domain.rules_engine import RulesViolationError

logger = logging.getLogger(__name__)

_AI_TYPES: frozenset[PlayerType] = frozenset(
    {PlayerType.AI_EASY, PlayerType.AI_MEDIUM, PlayerType.AI_HARD}
)

_MAX_RETRIES: int = 3


class TurnManager:
    """Listens for ``TurnChanged`` events and dispatches AI moves asynchronously.

    When an AI player's turn begins, ``TurnManager`` submits a move-request to a
    ``ThreadPoolExecutor`` and stores the resulting ``Future``.  The game loop
    calls ``collect_ai_result()`` each frame; once the ``Future`` is complete the
    move is submitted to the ``GameController``.  If the controller rejects the
    move, the manager retries up to ``_MAX_RETRIES`` times before logging a
    ``CRITICAL`` error.
    """

    def __init__(
        self,
        game_controller: Any,
        event_bus: EventBus,
        ai_orchestrator: Any,
    ) -> None:
        """Initialise the turn manager and subscribe to ``TurnChanged`` events.

        Args:
            game_controller: The ``GameController`` instance.
            event_bus: The shared ``EventBus``.
            ai_orchestrator: Object with a ``request_move(state, difficulty)``
                method that returns a ``Future[Move]``.
        """
        self._controller = game_controller
        self._event_bus = event_bus
        self._ai_orchestrator = ai_orchestrator
        self._ai_future: Future[Move] | None = None
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=1)

        event_bus.subscribe(TurnChanged, self._on_turn_changed)

    # ------------------------------------------------------------------
    # Event handler
    # ------------------------------------------------------------------

    def _on_turn_changed(self, event: TurnChanged) -> None:
        """Handle a ``TurnChanged`` event.

        If the newly active player is an AI type, enqueue a move request.
        """
        state = self._controller.current_state
        active_player = next(
            (p for p in state.players if p.side == event.active_player), None
        )
        if active_player is None:
            return
        if active_player.player_type not in _AI_TYPES:
            return

        # Submit the AI move request asynchronously.
        self._ai_future = self._ai_orchestrator.request_move(
            state, active_player.player_type
        )

    # ------------------------------------------------------------------
    # Game-loop hook
    # ------------------------------------------------------------------

    def collect_ai_result(self) -> None:
        """Collect a completed AI ``Future`` and submit the move to the controller.

        Called from the game loop's ``_update()`` phase.  Is a no-op if no
        ``Future`` is pending or the ``Future`` has not yet completed.

        On ``RulesViolationError`` the move is retried up to ``_MAX_RETRIES``
        times.  After all retries are exhausted a ``CRITICAL`` log entry is
        emitted.
        """
        if self._ai_future is None or not self._ai_future.done():
            return

        future = self._ai_future
        self._ai_future = None

        ai_move: Move = future.result()

        for attempt in range(_MAX_RETRIES):
            cmd = MovePiece(from_pos=ai_move.from_pos, to_pos=ai_move.to_pos)
            try:
                self._controller.submit_command(cmd)
                return  # success
            except RulesViolationError:
                logger.warning(
                    "TurnManager: AI move rejected (attempt %d/%d): %r",
                    attempt + 1,
                    _MAX_RETRIES,
                    ai_move,
                )

        logging.critical(
            "TurnManager: AI failed to produce a legal move after %d attempts. "
            "Possible deadlock.",
            _MAX_RETRIES,
        )
