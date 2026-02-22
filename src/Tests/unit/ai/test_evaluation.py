"""
test_evaluation.py — Unit tests for src/ai/evaluation.py

Epic: EPIC-5 | User Stories: US-501, US-502
Covers acceptance criteria:
  US-501: AC-1 (material score), AC-2 (flag safety), AC-3 (info advantage),
          AC-4 (terminal win), AC-5 (terminal loss), AC-6 (piece values)
  TASK-501: all 12 piece values, material_score() sum
  TASK-502: flag safety, info advantage, evaluate() aggregation
  TASK-503: order_moves() – captures before non-captures, flag-approach ordering
Specification: ai_strategy.md §6, §7
"""
from __future__ import annotations

import pytest

try:
    from src.ai.evaluation import (
        PIECE_VALUES,
        evaluate,
        flag_safety_score,
        info_advantage_score,
        material_score,
        mobility_score,
        order_moves,
    )
    _EVALUATION_AVAILABLE = True
except ImportError:
    _EVALUATION_AVAILABLE = False
    PIECE_VALUES = None  # type: ignore[assignment]
    evaluate = None  # type: ignore[assignment]
    flag_safety_score = None  # type: ignore[assignment]
    info_advantage_score = None  # type: ignore[assignment]
    material_score = None  # type: ignore[assignment]
    mobility_score = None  # type: ignore[assignment]
    order_moves = None  # type: ignore[assignment]

from src.domain.board import Board
from src.domain.enums import GamePhase, MoveType, PlayerSide, PlayerType, Rank
from src.domain.game_state import GameState
from src.domain.move import Move
from src.domain.piece import Piece, Position
from src.domain.player import Player

pytestmark = pytest.mark.xfail(
    not _EVALUATION_AVAILABLE,
    reason="src/ai/evaluation.py not yet implemented",
    strict=False,
)

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

_WIN_SENTINEL = 1_000_000
_LOSS_SENTINEL = -1_000_000


def _make_piece(
    rank: Rank,
    owner: PlayerSide,
    row: int,
    col: int,
    *,
    revealed: bool = False,
    has_moved: bool = False,
) -> Piece:
    return Piece(
        rank=rank, owner=owner, revealed=revealed, has_moved=has_moved, position=Position(row, col)
    )


def _make_player(side: PlayerSide, pieces: tuple[Piece, ...]) -> Player:
    flag_pos = next((p.position for p in pieces if p.rank == Rank.FLAG), None)
    return Player(
        side=side,
        player_type=PlayerType.HUMAN,
        pieces_remaining=pieces,
        flag_position=flag_pos,
    )


def _make_state(
    red_pieces: list[Piece],
    blue_pieces: list[Piece],
    phase: GamePhase = GamePhase.PLAYING,
    winner: PlayerSide | None = None,
) -> GameState:
    board = Board.create_empty()
    for p in red_pieces + blue_pieces:
        board = board.place_piece(p)
    red_player = _make_player(PlayerSide.RED, tuple(red_pieces))
    blue_player = _make_player(PlayerSide.BLUE, tuple(blue_pieces))
    return GameState(
        board=board,
        players=(red_player, blue_player),
        active_player=PlayerSide.RED,
        phase=phase,
        turn_number=1,
        winner=winner,
    )


@pytest.fixture
def simple_playing_state() -> GameState:
    """Minimal PLAYING state: each side has a Flag and a Scout."""
    red_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0),
        _make_piece(Rank.SCOUT, PlayerSide.RED, 8, 0, has_moved=True),
    ]
    blue_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0),
        _make_piece(Rank.SCOUT, PlayerSide.BLUE, 1, 0, has_moved=True),
    ]
    return _make_state(red_pieces, blue_pieces)


@pytest.fixture
def terminal_win_state() -> GameState:
    """GAME_OVER state where RED (AI) won."""
    red_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0),
        _make_piece(Rank.MARSHAL, PlayerSide.RED, 8, 0),
    ]
    blue_pieces: list[Piece] = []
    return _make_state(red_pieces, blue_pieces, phase=GamePhase.GAME_OVER, winner=PlayerSide.RED)


@pytest.fixture
def terminal_loss_state() -> GameState:
    """GAME_OVER state where BLUE won (RED/AI lost)."""
    red_pieces: list[Piece] = []
    blue_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0),
        _make_piece(Rank.MARSHAL, PlayerSide.BLUE, 1, 0),
    ]
    return _make_state(red_pieces, blue_pieces, phase=GamePhase.GAME_OVER, winner=PlayerSide.BLUE)


@pytest.fixture
def state_with_marshal() -> GameState:
    """State where RED has a Marshal (used to test material score increase)."""
    red_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0),
        _make_piece(Rank.MARSHAL, PlayerSide.RED, 8, 0),
    ]
    blue_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0),
        _make_piece(Rank.SCOUT, PlayerSide.BLUE, 1, 0),
    ]
    return _make_state(red_pieces, blue_pieces)


@pytest.fixture
def state_without_marshal() -> GameState:
    """State where RED has only a Scout and Flag (no Marshal)."""
    red_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0),
        _make_piece(Rank.SCOUT, PlayerSide.RED, 8, 0),
    ]
    blue_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0),
        _make_piece(Rank.SCOUT, PlayerSide.BLUE, 1, 0),
    ]
    return _make_state(red_pieces, blue_pieces)


@pytest.fixture
def flag_surrounded_by_bombs_state() -> GameState:
    """State where RED's Flag is surrounded by 3 Bombs (high flag safety)."""
    red_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0),
        _make_piece(Rank.BOMB, PlayerSide.RED, 8, 0),
        _make_piece(Rank.BOMB, PlayerSide.RED, 9, 1),
        _make_piece(Rank.BOMB, PlayerSide.RED, 8, 1),
        _make_piece(Rank.SCOUT, PlayerSide.RED, 7, 0),
    ]
    blue_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0),
        _make_piece(Rank.SCOUT, PlayerSide.BLUE, 4, 9),  # far away
    ]
    return _make_state(red_pieces, blue_pieces)


@pytest.fixture
def all_revealed_state() -> GameState:
    """State where all BLUE pieces are revealed (zero info-advantage penalty for RED)."""
    red_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0),
        _make_piece(Rank.SCOUT, PlayerSide.RED, 8, 0),
    ]
    blue_pieces = [
        _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0, revealed=True),
        _make_piece(Rank.SCOUT, PlayerSide.BLUE, 1, 0, revealed=True),
    ]
    return _make_state(red_pieces, blue_pieces)


# ---------------------------------------------------------------------------
# TASK-501 / US-501 AC-6: Piece value table
# ---------------------------------------------------------------------------


class TestPieceValues:
    """US-501 AC-6: Piece values must match ai_strategy.md §6.2."""

    @pytest.mark.parametrize(
        "rank, expected_value",
        [
            (Rank.MARSHAL, 10),
            (Rank.GENERAL, 9),
            (Rank.COLONEL, 8),
            (Rank.MAJOR, 7),
            (Rank.CAPTAIN, 6),
            (Rank.LIEUTENANT, 5),
            (Rank.SERGEANT, 4),
            (Rank.MINER, 8),   # above raw rank – essential for defusing bombs
            (Rank.SCOUT, 3),
            (Rank.SPY, 6),     # above raw rank – kills Marshal
            (Rank.BOMB, 7),
            (Rank.FLAG, _WIN_SENTINEL),
        ],
        ids=lambda x: x.name if isinstance(x, Rank) else str(x),
    )
    def test_piece_value_matches_specification(self, rank: Rank, expected_value: float) -> None:
        """Each rank's strategic value must match ai_strategy.md §6.2."""
        assert PIECE_VALUES[rank] == expected_value

    def test_miner_value_exceeds_raw_rank(self) -> None:
        """Miner's strategic value (8) must be greater than its raw rank value (3)."""
        assert PIECE_VALUES[Rank.MINER] > Rank.MINER.value

    def test_spy_value_exceeds_raw_rank(self) -> None:
        """Spy's strategic value (6) must be greater than its raw rank value (1)."""
        assert PIECE_VALUES[Rank.SPY] > Rank.SPY.value

    def test_marshal_is_highest_moveable_value(self) -> None:
        """Marshal has the highest strategic value among moveable pieces."""
        moveable_values = {
            rank: PIECE_VALUES[rank]
            for rank in Rank
            if rank not in (Rank.FLAG, Rank.BOMB)
        }
        assert PIECE_VALUES[Rank.MARSHAL] == max(moveable_values.values())


# ---------------------------------------------------------------------------
# TASK-501: material_score()
# ---------------------------------------------------------------------------


class TestMaterialScore:
    """material_score() sums PIECE_VALUES for all living pieces of a given side."""

    def test_material_score_sums_piece_values(self, state_with_marshal: GameState) -> None:
        """material_score returns the sum of PIECE_VALUES for all RED pieces."""
        expected = PIECE_VALUES[Rank.FLAG] + PIECE_VALUES[Rank.MARSHAL]
        assert material_score(state_with_marshal, PlayerSide.RED) == expected

    def test_material_score_increases_with_marshal(
        self,
        state_with_marshal: GameState,
        state_without_marshal: GameState,
    ) -> None:
        """US-501 AC-1: Score is higher when AI has captured opponent's Marshal."""
        score_with = material_score(state_with_marshal, PlayerSide.RED)
        score_without = material_score(state_without_marshal, PlayerSide.RED)
        assert score_with > score_without

    def test_material_score_both_sides_independent(self, simple_playing_state: GameState) -> None:
        """Material score is computed independently per side."""
        red_score = material_score(simple_playing_state, PlayerSide.RED)
        blue_score = material_score(simple_playing_state, PlayerSide.BLUE)
        # Both sides have Flag + Scout: same piece set, same score
        assert red_score == blue_score

    def test_material_score_zero_for_empty_side(self) -> None:
        """material_score returns 0 when a side has no pieces remaining."""
        red_pieces: list[Piece] = []
        blue_pieces = [
            _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0),
        ]
        state = _make_state(
            red_pieces, blue_pieces, phase=GamePhase.GAME_OVER, winner=PlayerSide.BLUE
        )
        assert material_score(state, PlayerSide.RED) == 0


# ---------------------------------------------------------------------------
# TASK-502 / US-501 AC-2: flag_safety_score()
# ---------------------------------------------------------------------------


class TestFlagSafetyScore:
    """flag_safety_score() reflects bomb coverage and opponent distance."""

    def test_flag_safety_higher_when_bombs_surround_flag(
        self,
        flag_surrounded_by_bombs_state: GameState,
        simple_playing_state: GameState,
    ) -> None:
        """US-501 AC-2: Flag surrounded by Bombs yields a higher safety score."""
        score_fortified = flag_safety_score(flag_surrounded_by_bombs_state, PlayerSide.RED)
        score_open = flag_safety_score(simple_playing_state, PlayerSide.RED)
        assert score_fortified > score_open

    def test_flag_safety_increases_with_distance_to_enemy(self) -> None:
        """Flag is safer when the nearest enemy is farther away."""
        # Enemy piece close to RED's flag
        red_near = [
            _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0),
            _make_piece(Rank.SCOUT, PlayerSide.RED, 8, 0),
        ]
        blue_near = [
            _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0),
            _make_piece(Rank.SCOUT, PlayerSide.BLUE, 7, 0, has_moved=True),  # 2 rows away
        ]
        state_near = _make_state(red_near, blue_near)

        # Enemy piece far from RED's flag
        red_far = [
            _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0),
            _make_piece(Rank.SCOUT, PlayerSide.RED, 8, 0),
        ]
        blue_far = [
            _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0),
            _make_piece(Rank.SCOUT, PlayerSide.BLUE, 0, 9, has_moved=True),  # far corner
        ]
        state_far = _make_state(red_far, blue_far)

        score_near = flag_safety_score(state_near, PlayerSide.RED)
        score_far = flag_safety_score(state_far, PlayerSide.RED)
        assert score_far > score_near


# ---------------------------------------------------------------------------
# TASK-502 / US-501 AC-3: info_advantage_score()
# ---------------------------------------------------------------------------


class TestInfoAdvantageScore:
    """info_advantage_score() penalises uncertainty about opponent piece ranks."""

    def test_info_advantage_zero_when_all_opponent_pieces_revealed(
        self, all_revealed_state: GameState
    ) -> None:
        """US-501 AC-3: No penalty when all opponent pieces are revealed."""
        score = info_advantage_score(all_revealed_state, PlayerSide.RED)
        assert score == 0.0

    def test_info_advantage_negative_when_unrevealed_pieces_exist(
        self, simple_playing_state: GameState
    ) -> None:
        """Unrevealed opponent pieces incur a negative information penalty."""
        score = info_advantage_score(simple_playing_state, PlayerSide.RED)
        assert score <= 0.0

    def test_info_advantage_more_negative_with_more_unrevealed_pieces(self) -> None:
        """Penalty grows as more opponent pieces remain unrevealed."""
        # Few unrevealed pieces
        red_pieces = [_make_piece(Rank.FLAG, PlayerSide.RED, 9, 0)]
        blue_few_unrevealed = [
            _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0, revealed=True),
            _make_piece(Rank.SCOUT, PlayerSide.BLUE, 1, 0, revealed=True),
            _make_piece(Rank.MINER, PlayerSide.BLUE, 1, 1, revealed=False),
        ]
        state_few = _make_state(red_pieces, blue_few_unrevealed)

        # Many unrevealed pieces
        blue_many_unrevealed = [
            _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0, revealed=False),
            _make_piece(Rank.SCOUT, PlayerSide.BLUE, 1, 0, revealed=False),
            _make_piece(Rank.MINER, PlayerSide.BLUE, 1, 1, revealed=False),
            _make_piece(Rank.SERGEANT, PlayerSide.BLUE, 2, 0, revealed=False),
            _make_piece(Rank.CAPTAIN, PlayerSide.BLUE, 2, 1, revealed=False),
        ]
        state_many = _make_state(red_pieces, blue_many_unrevealed)

        score_few = info_advantage_score(state_few, PlayerSide.RED)
        score_many = info_advantage_score(state_many, PlayerSide.RED)
        assert score_many < score_few


# ---------------------------------------------------------------------------
# TASK-502 / US-501 AC-4 & AC-5: evaluate() terminal states
# ---------------------------------------------------------------------------


class TestEvaluateTerminalStates:
    """evaluate() must return sentinel values for finished games."""

    def test_terminal_win_returns_positive_sentinel(
        self, terminal_win_state: GameState
    ) -> None:
        """US-501 AC-4: evaluate() returns +1_000_000 when AI wins."""
        score = evaluate(terminal_win_state, PlayerSide.RED)
        assert score == _WIN_SENTINEL

    def test_terminal_loss_returns_negative_sentinel(
        self, terminal_loss_state: GameState
    ) -> None:
        """US-501 AC-5: evaluate() returns -1_000_000 when AI loses."""
        score = evaluate(terminal_loss_state, PlayerSide.RED)
        assert score == _LOSS_SENTINEL

    def test_terminal_win_perspective_is_ai_side_dependent(
        self, terminal_win_state: GameState
    ) -> None:
        """From BLUE's perspective, RED winning is a loss (returns -1_000_000)."""
        score = evaluate(terminal_win_state, PlayerSide.BLUE)
        assert score == _LOSS_SENTINEL

    def test_non_terminal_state_returns_heuristic(
        self, simple_playing_state: GameState
    ) -> None:
        """Non-terminal states return a finite heuristic value, not a sentinel."""
        score = evaluate(simple_playing_state, PlayerSide.RED)
        assert score != _WIN_SENTINEL
        assert score != _LOSS_SENTINEL


# ---------------------------------------------------------------------------
# TASK-502: evaluate() weighted aggregation
# ---------------------------------------------------------------------------


class TestEvaluateWeightedAggregation:
    """evaluate() combines material, mobility, flag safety, and info advantage."""

    def test_evaluate_returns_float(self, simple_playing_state: GameState) -> None:
        """evaluate() must return a numeric (float) value."""
        result = evaluate(simple_playing_state, PlayerSide.RED)
        assert isinstance(result, float | int)

    def test_evaluate_favours_more_material(
        self,
        state_with_marshal: GameState,
        state_without_marshal: GameState,
    ) -> None:
        """All else equal, having a Marshal gives a higher evaluation score."""
        score_with = evaluate(state_with_marshal, PlayerSide.RED)
        score_without = evaluate(state_without_marshal, PlayerSide.RED)
        assert score_with > score_without


# ---------------------------------------------------------------------------
# TASK-503 / US-502: order_moves()
# ---------------------------------------------------------------------------


class TestOrderMoves:
    """order_moves() prioritises captures, then flag-approach, then others."""

    def _make_scout_move(
        self,
        from_row: int,
        from_col: int,
        to_row: int,
        to_col: int,
        owner: PlayerSide = PlayerSide.RED,
        move_type: MoveType = MoveType.MOVE,
    ) -> Move:
        piece = _make_piece(Rank.SCOUT, owner, from_row, from_col, has_moved=True)
        return Move(
            piece=piece,
            from_pos=Position(from_row, from_col),
            to_pos=Position(to_row, to_col),
            move_type=move_type,
        )

    def _make_attack_move(
        self,
        attacker_rank: Rank,
        from_row: int,
        from_col: int,
        to_row: int,
        to_col: int,
        target_rank: Rank = Rank.SCOUT,
    ) -> Move:
        piece = _make_piece(attacker_rank, PlayerSide.RED, from_row, from_col, has_moved=True)
        return Move(
            piece=piece,
            from_pos=Position(from_row, from_col),
            to_pos=Position(to_row, to_col),
            move_type=MoveType.ATTACK,
        )

    def test_captures_ordered_before_non_captures(self, simple_playing_state: GameState) -> None:
        """TASK-503: Capture moves must appear before non-capture moves."""
        normal_move = self._make_scout_move(8, 0, 7, 0, move_type=MoveType.MOVE)
        capture_move = self._make_attack_move(Rank.SCOUT, 8, 0, 1, 0)
        mixed = [normal_move, capture_move]

        ordered = order_moves(mixed, simple_playing_state, PlayerSide.RED)

        capture_idx = ordered.index(capture_move)
        normal_idx = ordered.index(normal_move)
        assert capture_idx < normal_idx

    def test_higher_value_capture_ordered_before_lower_value_capture(
        self, simple_playing_state: GameState
    ) -> None:
        """Higher-value captures (e.g., Marshal) appear before lower-value ones."""
        capture_scout = self._make_attack_move(Rank.MARSHAL, 8, 5, 1, 0, target_rank=Rank.SCOUT)
        capture_marshal = self._make_attack_move(Rank.SCOUT, 8, 0, 1, 5, target_rank=Rank.MARSHAL)

        # We need a state where the board has the target pieces
        red_pieces = [
            _make_piece(Rank.FLAG, PlayerSide.RED, 9, 0),
            _make_piece(Rank.MARSHAL, PlayerSide.RED, 8, 5),
            _make_piece(Rank.SCOUT, PlayerSide.RED, 8, 0),
        ]
        blue_pieces = [
            _make_piece(Rank.FLAG, PlayerSide.BLUE, 0, 0),
            _make_piece(Rank.MARSHAL, PlayerSide.BLUE, 1, 5),
            _make_piece(Rank.SCOUT, PlayerSide.BLUE, 1, 0),
        ]
        state = _make_state(red_pieces, blue_pieces)

        ordered = order_moves([capture_scout, capture_marshal], state, PlayerSide.RED)
        # capture_marshal (attacking MARSHAL) should come first
        assert ordered[0].to_pos == Position(1, 5)

    def test_order_moves_returns_all_input_moves(
        self, simple_playing_state: GameState
    ) -> None:
        """order_moves must return exactly the same moves as input (no additions/omissions)."""
        moves = [
            self._make_scout_move(8, 0, 7, 0),
            self._make_scout_move(8, 0, 8, 1),
            self._make_attack_move(Rank.SCOUT, 8, 0, 1, 0),
        ]
        ordered = order_moves(moves, simple_playing_state, PlayerSide.RED)
        assert len(ordered) == len(moves)
        assert set(id(m) for m in ordered) == set(id(m) for m in moves)
