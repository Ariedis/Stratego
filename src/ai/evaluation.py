"""
src/ai/evaluation.py

Evaluation function and move ordering for the Stratego AI.
Specification: ai_strategy.md §6, §7
"""
from __future__ import annotations

from src.domain.enums import MoveType, PlayerSide, Rank
from src.domain.game_state import GameState
from src.domain.move import Move
from src.domain.rules_engine import generate_moves

# ---------------------------------------------------------------------------
# Piece value table  (ai_strategy.md §6.2)
# ---------------------------------------------------------------------------

#: Strategic piece values, reflecting community knowledge and AI research.
#: FLAG uses a large sentinel (game-ending); Miner/Spy exceed their raw rank.
PIECE_VALUES: dict[Rank, float] = {
    Rank.FLAG: 1_000_000,
    Rank.BOMB: 7,
    Rank.MARSHAL: 10,
    Rank.GENERAL: 9,
    Rank.COLONEL: 8,
    Rank.MAJOR: 7,
    Rank.CAPTAIN: 6,
    Rank.LIEUTENANT: 5,
    Rank.SERGEANT: 4,
    Rank.MINER: 8,
    Rank.SCOUT: 3,
    Rank.SPY: 6,
}

_WIN_SENTINEL: float = 1_000_000.0
_LOSS_SENTINEL: float = -1_000_000.0

# Weights for the weighted-sum aggregation (ai_strategy.md §6.1).
_MATERIAL_WEIGHT: float = 0.50
_MOBILITY_WEIGHT: float = 0.10
_FLAG_SAFETY_WEIGHT: float = 0.25
_INFO_ADVANTAGE_WEIGHT: float = 0.15

# Scaling factors for individual sub-scores.
_FLAG_DIST_WEIGHT: float = 1.0
_BOMB_COVERAGE_WEIGHT: float = 2.0
_UNREVEALED_PENALTY: float = 1.0


# ---------------------------------------------------------------------------
# Sub-score functions
# ---------------------------------------------------------------------------


def material_score(state: GameState, side: PlayerSide) -> float:
    """Return the sum of PIECE_VALUES for all living pieces belonging to *side*.

    Specification: ai_strategy.md §6.1 (Material component, weight 40 %).
    """
    for player in state.players:
        if player.side == side:
            return sum(PIECE_VALUES[p.rank] for p in player.pieces_remaining)
    return 0.0


def mobility_score(state: GameState, side: PlayerSide) -> float:
    """Return the count of legal moves available to *side*'s pieces.

    Specification: ai_strategy.md §6.1 (Mobility component, weight 20 %).
    """
    return float(len(generate_moves(state, side)))


def flag_safety_score(state: GameState, side: PlayerSide) -> float:
    """Return a score reflecting how well *side*'s Flag is protected.

    Score = distance × weight + bomb_coverage_count × weight.
    A higher score means the Flag is safer (further from enemies, more Bombs nearby).

    Specification: ai_strategy.md §6.1 (Flag safety component, weight 25 %).
    """
    opponent = PlayerSide.BLUE if side == PlayerSide.RED else PlayerSide.RED

    # Locate our Flag.
    flag_pos = None
    for player in state.players:
        if player.side == side:
            flag_pos = player.flag_position
            break
    if flag_pos is None:
        return 0.0

    # Count Bombs adjacent to the Flag (orthogonal + diagonal, 8 neighbours).
    bomb_count = 0
    for player in state.players:
        if player.side == side:
            for piece in player.pieces_remaining:
                if piece.rank == Rank.BOMB:
                    dr = abs(piece.position.row - flag_pos.row)
                    dc = abs(piece.position.col - flag_pos.col)
                    if dr <= 1 and dc <= 1 and (dr + dc) > 0:
                        bomb_count += 1

    # Find closest opponent moveable piece (Manhattan distance).
    min_distance = 20  # larger than any possible board distance
    for player in state.players:
        if player.side == opponent:
            for piece in player.pieces_remaining:
                if piece.rank in (Rank.BOMB, Rank.FLAG):
                    continue
                dist = abs(piece.position.row - flag_pos.row) + abs(
                    piece.position.col - flag_pos.col
                )
                if dist < min_distance:
                    min_distance = dist

    return (min_distance * _FLAG_DIST_WEIGHT) + (bomb_count * _BOMB_COVERAGE_WEIGHT)


def info_advantage_score(state: GameState, ai_side: PlayerSide) -> float:
    """Return an information-advantage score (penalty for opponent uncertainty).

    Each unrevealed opponent piece contributes a negative penalty.
    Score = -(unrevealed_count × weight).

    Specification: ai_strategy.md §6.1 (Information advantage, weight 15 %).
    """
    opponent = PlayerSide.BLUE if ai_side == PlayerSide.RED else PlayerSide.RED
    unrevealed = 0
    for player in state.players:
        if player.side == opponent:
            for piece in player.pieces_remaining:
                if not piece.revealed:
                    unrevealed += 1
    return -(unrevealed * _UNREVEALED_PENALTY)


# ---------------------------------------------------------------------------
# Terminal / aggregate evaluation
# ---------------------------------------------------------------------------


def evaluate(state: GameState, ai_side: PlayerSide) -> float:
    """Return a scalar heuristic score of *state* from *ai_side*'s perspective.

    Returns +1_000_000 on a win for ai_side and -1_000_000 on a loss.
    For non-terminal states, returns a weighted sum of four components:
      material × 0.40 + mobility × 0.20 + flag_safety × 0.25 + info × 0.15.

    Specification: ai_strategy.md §6.1.
    """
    from src.domain.enums import GamePhase

    if state.phase == GamePhase.GAME_OVER:
        if state.winner == ai_side:
            return _WIN_SENTINEL
        if state.winner is not None:
            return _LOSS_SENTINEL
        # Draw
        return 0.0

    mat = material_score(state, ai_side)
    mob = mobility_score(state, ai_side)
    flag = flag_safety_score(state, ai_side)
    info = info_advantage_score(state, ai_side)

    return (
        _MATERIAL_WEIGHT * mat
        + _MOBILITY_WEIGHT * mob
        + _FLAG_SAFETY_WEIGHT * flag
        + _INFO_ADVANTAGE_WEIGHT * info
    )


# ---------------------------------------------------------------------------
# Move ordering  (ai_strategy.md §7)
# ---------------------------------------------------------------------------


def order_moves(
    moves: list[Move], state: GameState, ai_side: PlayerSide
) -> list[Move]:
    """Return *moves* sorted from most promising to least promising.

    Order:
    1. Capture moves (ATTACK), sorted by target piece value descending.
    2. Flag-approach moves: reduce Manhattan distance to estimated opponent Flag.
    3. All others (probe / random moves).

    Specification: ai_strategy.md §7.
    """
    opponent = PlayerSide.BLUE if ai_side == PlayerSide.RED else PlayerSide.RED

    # Locate the estimated opponent Flag position (use known flag_position if revealed).
    opp_flag_pos = None
    for player in state.players:
        if player.side == opponent:
            opp_flag_pos = player.flag_position
            break

    captures: list[tuple[float, Move]] = []
    flag_approaches: list[Move] = []
    others: list[Move] = []

    for move in moves:
        if move.move_type == MoveType.ATTACK:
            dest_sq = state.board.get_square(move.to_pos)
            target_value = 0.0
            if dest_sq.piece is not None:
                target_value = PIECE_VALUES.get(dest_sq.piece.rank, 0.0)
            captures.append((target_value, move))
        else:
            # Check if this move approaches the opponent Flag.
            if opp_flag_pos is not None:
                dist_before = abs(move.from_pos.row - opp_flag_pos.row) + abs(
                    move.from_pos.col - opp_flag_pos.col
                )
                dist_after = abs(move.to_pos.row - opp_flag_pos.row) + abs(
                    move.to_pos.col - opp_flag_pos.col
                )
                if dist_after < dist_before:
                    flag_approaches.append(move)
                    continue
            others.append(move)

    # Sort captures by target value descending.
    captures.sort(key=lambda x: x[0], reverse=True)
    sorted_captures = [m for _, m in captures]

    return sorted_captures + flag_approaches + others
