"""
src/ai/minimax.py

Minimax with alpha-beta pruning and iterative deepening for the Stratego AI.
Specification: ai_strategy.md §4.2
"""
from __future__ import annotations

import time
from math import inf
from typing import Any

from src.domain.enums import GamePhase, PlayerSide
from src.domain.game_state import GameState
from src.domain.move import Move
from src.domain.rules_engine import RulesViolationError, apply_move, generate_moves


def _other_side(side: PlayerSide) -> PlayerSide:
    """Return the opposing side."""
    return PlayerSide.BLUE if side == PlayerSide.RED else PlayerSide.RED


_TT_MAX_SIZE: int = 200_000  # Maximum transposition-table entries before clearing.


def _board_key(state: GameState) -> tuple[Any, PlayerSide]:
    """Return a compact, history-independent hash key for transposition-table lookup.

    Encodes only the board piece layout and active player — ignoring move history
    and turn counter — so transpositions (same position reached via different move
    sequences) hit the same cache entry.
    """
    pieces_key = tuple(sorted(
        (sq.piece.position.row, sq.piece.position.col,
         sq.piece.rank, sq.piece.owner, sq.piece.revealed)
        for sq in state.board.squares.values()
        if sq.piece is not None
    ))
    return (pieces_key, state.active_player)


def _alpha_beta(
    state: GameState,
    depth: int,
    ai_side: PlayerSide,
    alpha: float,
    beta: float,
    maximising: bool,
    deadline: float | None,
    use_move_ordering: bool,
    _tt: dict[tuple[Any, PlayerSide], tuple[float, int, str]],
) -> float:
    """Recursive alpha-beta helper. Returns a heuristic score."""
    from src.ai.evaluation import evaluate, order_moves

    # Base case: terminal state or depth exhausted — count only leaf evaluations.
    if depth == 0 or state.phase == GamePhase.GAME_OVER:
        minimax.node_count += 1  # type: ignore[attr-defined]
        return evaluate(state, ai_side)

    # Transposition-table lookup.
    tt_key = _board_key(state)
    if tt_key in _tt:
        tt_score, tt_depth, tt_flag = _tt[tt_key]
        if tt_depth >= depth:
            if tt_flag == "exact":
                return tt_score
            if tt_flag == "lower" and tt_score >= beta:
                return tt_score
            if tt_flag == "upper" and tt_score <= alpha:
                return tt_score

    original_alpha = alpha
    current_side = ai_side if maximising else _other_side(ai_side)
    moves = generate_moves(state, current_side)

    if not moves:
        return evaluate(state, ai_side)

    if use_move_ordering:
        moves = order_moves(moves, state, current_side)

    if maximising:
        best_score = -inf
        for move in moves:
            if deadline is not None and time.monotonic() > deadline:
                break
            try:
                next_state = apply_move(state, move)
            except RulesViolationError:
                continue
            score = _alpha_beta(
                next_state, depth - 1, ai_side, alpha, beta, False, deadline,
                use_move_ordering, _tt,
            )
            if score > best_score:
                best_score = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break  # Beta cut-off
    else:
        best_score = inf
        for move in moves:
            if deadline is not None and time.monotonic() > deadline:
                break
            try:
                next_state = apply_move(state, move)
            except RulesViolationError:
                continue
            score = _alpha_beta(
                next_state, depth - 1, ai_side, alpha, beta, True, deadline,
                use_move_ordering, _tt,
            )
            if score < best_score:
                best_score = score
            if score < beta:
                beta = score
            if beta <= alpha:
                break  # Alpha cut-off

    # Store result in transposition table.
    if len(_tt) < _TT_MAX_SIZE:
        if best_score <= original_alpha:
            flag = "upper"
        elif best_score >= beta:
            flag = "lower"
        else:
            flag = "exact"
        _tt[tt_key] = (best_score, depth, flag)

    return best_score


def minimax(
    state: GameState,
    depth: int,
    ai_side: PlayerSide,
    alpha: float = -inf,
    beta: float = inf,
    deadline: float | None = None,
    use_move_ordering: bool = True,
    _tt: dict[tuple[Any, PlayerSide], tuple[float, int, str]] | None = None,
) -> Move | None:
    """Return the best Move for *ai_side* in *state* using minimax with alpha-beta pruning.

    Returns None if the game is already over or no legal moves exist.
    *deadline* is an absolute time (from time.monotonic()); search is interrupted
    when exceeded and the best move found so far is returned.

    The node_count attribute is updated on each call and can be read as
    ``minimax.node_count`` after a search completes.

    *_tt* is the transposition table shared across iterative-deepening depths.
    When ``None`` a fresh empty table is created.

    Specification: ai_strategy.md §4.2.
    """
    from src.ai.evaluation import order_moves

    minimax.node_count = 0  # type: ignore[attr-defined]
    if _tt is None:
        _tt = {}

    if state.phase == GamePhase.GAME_OVER:
        return None

    moves = generate_moves(state, ai_side)
    if not moves:
        return None

    if use_move_ordering:
        moves = order_moves(moves, state, ai_side)

    best_move_found: Move | None = None
    best_score = -inf

    for move in moves:
        if deadline is not None and time.monotonic() > deadline:
            break
        try:
            next_state = apply_move(state, move)
        except RulesViolationError:
            continue
        score = _alpha_beta(
            next_state, depth - 1, ai_side, alpha, beta, False, deadline,
            use_move_ordering, _tt,
        )
        if score > best_score or best_move_found is None:
            best_score = score
            best_move_found = move
        if score > alpha:
            alpha = score

    return best_move_found


# Initialise the node_count attribute so it is always accessible.
minimax.node_count = 0  # type: ignore[attr-defined]


def best_move(
    state: GameState,
    max_depth: int,
    deadline: float,
) -> Move | None:
    """Return the best move found via iterative deepening minimax.

    Searches at depths 1, 2, …, *max_depth*, returning the best move found at
    the deepest completed depth before *deadline*.  Always returns the depth-1
    result if time permits, ensuring a non-None result for reachable states.

    Specification: ai_strategy.md §4.2.
    """
    if state.phase == GamePhase.GAME_OVER:
        return None

    result: Move | None = None
    _tt: dict[tuple[Any, PlayerSide], tuple[float, int, str]] = {}  # Shared TT across all iterative-deepening depths.

    for depth in range(1, max_depth + 1):
        if time.monotonic() > deadline:
            break
        candidate = minimax(state, depth, state.active_player, deadline=deadline, _tt=_tt)
        if candidate is not None:
            result = candidate

    return result
