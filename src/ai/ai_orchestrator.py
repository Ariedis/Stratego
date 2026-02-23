"""
src/ai/ai_orchestrator.py

AI Orchestrator — selects the best move for a given difficulty level.
Specification: ai_strategy.md §8
"""
from __future__ import annotations

import time

from src.ai.minimax import best_move
from src.domain.enums import PlayerType
from src.domain.game_state import GameState
from src.domain.move import Move
from src.domain.rules_engine import ValidationResult, validate_move

#: Search depth mapped to each AI difficulty (ai_strategy.md §4.2).
DIFFICULTY_DEPTH: dict[PlayerType, int] = {
    PlayerType.AI_EASY: 2,
    PlayerType.AI_MEDIUM: 4,
    PlayerType.AI_HARD: 6,
}

#: Piece-count threshold below which the endgame depth boost activates.
_ENDGAME_PIECE_THRESHOLD: int = 10

#: Maximum retry attempts before raising AIMoveFailed.
_MAX_RETRIES: int = 3


class AIMoveFailed(Exception):
    """Raised when the AI cannot produce a legal move after all retries."""


class AIOrchestrator:
    """Selects the best move for the AI player at a given difficulty level.

    Wraps the minimax search with difficulty-to-depth mapping, endgame boost,
    time-limit enforcement, and retry logic for invalid moves.

    Specification: ai_strategy.md §8.
    """

    def request_move(
        self,
        state: GameState,
        player_type: PlayerType,
        time_limit_ms: int = 950,
    ) -> Move:
        """Return the best legal move for the AI side defined by *player_type*.

        Steps:
        1. Determine search depth from DIFFICULTY_DEPTH, boosted by 2 in endgame.
        2. Set a deadline from *time_limit_ms*.
        3. Call best_move(); validate the result.
        4. Retry up to _MAX_RETRIES times on invalid/None result.
        5. Raise AIMoveFailed after _MAX_RETRIES consecutive failures.

        Specification: ai_strategy.md §8.
        """
        depth = DIFFICULTY_DEPTH[player_type]

        # Endgame boost: total pieces across both sides < 10 → depth += 2.
        total_pieces = sum(len(player.pieces_remaining) for player in state.players)
        if total_pieces < _ENDGAME_PIECE_THRESHOLD:
            depth += 2

        deadline = time.monotonic() + (time_limit_ms / 1000.0)

        for _attempt in range(_MAX_RETRIES):
            candidate = best_move(state, max_depth=depth, deadline=deadline)

            if candidate is None:
                continue

            try:
                result = validate_move(state, candidate)
            except Exception:
                result = ValidationResult.INVALID

            if result == ValidationResult.OK:
                return candidate

            # Reset deadline for the next attempt.
            deadline = time.monotonic() + (time_limit_ms / 1000.0)

        raise AIMoveFailed("AI could not produce a legal move after 3 attempts.")
